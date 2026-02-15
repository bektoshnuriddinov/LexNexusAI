from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.dependencies import get_admin_user, User
from app.db.supabase import get_supabase_admin_client

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool = False


class UserResponse(BaseModel):
    id: str
    email: str
    is_admin: bool
    created_at: str


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    admin: User = Depends(get_admin_user)
) -> UserResponse:
    """Create a new user (admin only). Uses Supabase Admin API."""
    supabase_admin = get_supabase_admin_client()

    try:
        # Create user in auth.users via Admin API
        auth_response = supabase_admin.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True  # Auto-confirm email
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user in auth system"
            )

        user_id = auth_response.user.id

        # Create user profile
        profile_data = {
            "id": user_id,
            "email": request.email,
            "is_admin": request.is_admin,
            "created_by": admin.id
        }

        profile_response = supabase_admin.table("user_profiles").insert(profile_data).execute()

        if not profile_response.data:
            # Rollback: delete auth user if profile creation fails
            supabase_admin.auth.admin.delete_user(user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )

        profile = profile_response.data[0]

        return UserResponse(
            id=profile["id"],
            email=profile["email"],
            is_admin=profile["is_admin"],
            created_at=profile["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    admin: User = Depends(get_admin_user)
) -> list[UserResponse]:
    """List all users (admin only)."""
    supabase_admin = get_supabase_admin_client()

    try:
        response = supabase_admin.table("user_profiles").select("*").order("created_at", desc=True).execute()

        return [
            UserResponse(
                id=user["id"],
                email=user["email"],
                is_admin=user["is_admin"],
                created_at=user["created_at"]
            )
            for user in response.data
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


class ToggleAdminRequest(BaseModel):
    is_admin: bool


@router.patch("/users/{user_id}/admin", response_model=UserResponse)
async def toggle_admin_status(
    user_id: str,
    request: ToggleAdminRequest,
    admin: User = Depends(get_admin_user)
) -> UserResponse:
    """Toggle admin status for a user (admin only)."""
    supabase_admin = get_supabase_admin_client()

    try:
        # Update admin status
        response = supabase_admin.table("user_profiles").update({
            "is_admin": request.is_admin
        }).eq("id", user_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user = response.data[0]

        return UserResponse(
            id=user["id"],
            email=user["email"],
            is_admin=user["is_admin"],
            created_at=user["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update admin status: {str(e)}"
        )
