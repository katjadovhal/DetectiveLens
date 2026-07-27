from fastapi import APIRouter, HTTPException

from app import repositories as repo
from app.schemas import PurchaseHqItem, UpdateProfile

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


@router.get("/{user_id}/learning-insights")
async def learning_insights(user_id: str):
    try:
        return await repo.get_learning_insights_data(user_id)
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


@router.post("/{user_id}/hq/purchase")
def purchase_hq_item(body: PurchaseHqItem, user_id: str):
    try:
        return repo.purchase_hq_item(user_id, body.itemId)
    except ValueError as e:
        message = str(e)
        if message == "Profile not found":
            raise HTTPException(
                status_code=404,
                detail={"error": "NOT_FOUND", "message": message, "statusCode": 404},
            )
        status = 400
        error = "VALIDATION_ERROR"
        if message == "Not enough XP":
            error = "INSUFFICIENT_XP"
        elif message == "Already owned":
            error = "ALREADY_OWNED"
        raise HTTPException(
            status_code=status,
            detail={"error": error, "message": message, "statusCode": status},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )
