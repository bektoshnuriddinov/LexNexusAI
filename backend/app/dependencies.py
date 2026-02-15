from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

from app.config import get_settings
from app.db.supabase import get_supabase_client

security = HTTPBearer()


class User(BaseModel):
    id: str
    email: str | None = None
    is_admin: bool = False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Verify Supabase JWT token and extract user info, including admin status."""
    settings = get_settings()
    token = credentials.credentials
    supabase = get_supabase_client()

    try:
        payload = jwt.decode(
            token,
            settings.supabase_anon_key,
            algorithms=["HS256", "ES256"],
            options={"verify_signature": False},
            audience="authenticated"
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )

        # Query user_profiles for admin status
        try:
            response = supabase.table("user_profiles").select("is_admin").eq("id", user_id).single().execute()
            print(f"Supabase response for user_profiles query: {response}")
            is_admin = response.data.get("is_admin", False) if response.data else False
        except Exception as e:
            # If user_profiles table doesn't exist or query fails, user is not admin
            is_admin = False

        return User(id=user_id, email=email, is_admin=is_admin)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require the current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
