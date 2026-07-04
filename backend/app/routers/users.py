from fastapi import APIRouter, HTTPException

from app import repositories as repo

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def list_users():
    """Get list of all users for selecting existing users"""
    try:
        users = repo.get_all_users()
        return {
            "users": [
                {
                    "id": u["id"],
                    "username": u["username"],
                }
                for u in users
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )


@router.get("/{user_id}")
def get_user(user_id: str):
    """Get specific user data"""
    try:
        user = repo.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail={"error": "NOT_FOUND", "message": "User not found", "statusCode": 404},
            )
        profile = repo.get_profile(user_id)
        return {
            "user": {
                "id": user["id"],
                "username": user["username"],
            },
            "profile": {
                "avatarId": profile["avatarId"] if profile else None,
                "displayName": profile["displayName"] if profile else user["username"],
                "onboardingCompleted": profile["onboardingCompleted"] if profile else False,
            } if profile else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )

