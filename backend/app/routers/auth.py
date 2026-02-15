from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, User
from app.db.supabase import get_supabase_client

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """Get the current authenticated user's info."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
    }


@router.get("/debug/profile")
async def debug_profile(current_user: User = Depends(get_current_user)) -> dict:
    """Debug endpoint to check user_profiles table."""
    supabase = get_supabase_client()

    try:
        # Try to query user_profiles
        response = supabase.table("user_profiles").select("*").eq("id", current_user.id).execute()

        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "is_admin_from_token": current_user.is_admin,
            "user_profiles_query_success": True,
            "profile_data": response.data[0] if response.data else None,
            "all_profiles": supabase.table("user_profiles").select("email, is_admin").execute().data
        }
    except Exception as e:
        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "is_admin_from_token": current_user.is_admin,
            "user_profiles_query_success": False,
            "error": str(e)
        }
