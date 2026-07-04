from fastapi import APIRouter, HTTPException

from app import repositories as repo

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/{user_id}")
def get_home(user_id: str):
    try:
        return repo.get_home_data(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )
