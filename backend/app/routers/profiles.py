from fastapi import APIRouter, HTTPException

from app import repositories as repo
from app.schemas import UpdateProfile

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/{user_id}")
def get_profile(user_id: str):
    try:
        return repo.get_profile_data(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )


@router.patch("/{user_id}")
def update_profile(body: UpdateProfile, user_id: str):
    try:
        return repo.update_profile(user_id, body.model_dump(exclude_none=True))
    except ValueError as e:
        message = str(e)
        if "unlocks at" in message.lower():
            raise HTTPException(
                status_code=400,
                detail={"error": "VALIDATION_ERROR", "message": message, "statusCode": 400},
            )
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Profile not found", "statusCode": 404},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )
