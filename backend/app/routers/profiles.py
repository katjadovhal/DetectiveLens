from fastapi import APIRouter, HTTPException

from app import repositories as repo
from app.schemas import UpdateProfile

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/{user_id}")
@router.get("")
def get_profile(user_id: str | None = None):
    return repo.get_profile_data()


@router.patch("/{user_id}")
def update_profile(body: UpdateProfile, user_id: str = "demo-user-id"):
    try:
        return repo.update_profile(body.model_dump(exclude_none=True))
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Profile not found", "statusCode": 404},
        )
