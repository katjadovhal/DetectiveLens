from fastapi import APIRouter, HTTPException

from app import repositories as repo
from app.schemas import MarkNotificationRead, UpdateProfile

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


@router.get("/{user_id}/badges")
def get_badges(user_id: str):
    try:
        return repo.get_user_badges_data(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )


@router.get("/{user_id}/notifications")
def get_notifications(user_id: str):
    try:
        return repo.list_notifications(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )


@router.post("/{user_id}/notifications/read")
def read_notification(user_id: str, body: MarkNotificationRead):
    try:
        return repo.mark_notification_read(user_id, body.notificationId)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": str(e), "statusCode": 404},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )


@router.post("/{user_id}/notifications/read-all")
def read_all_notifications(user_id: str):
    try:
        return repo.mark_all_notifications_read(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )


@router.patch("/{user_id}")
def update_profile(body: UpdateProfile, user_id: str):
    try:
        return repo.update_profile(user_id, body.model_dump(exclude_none=True))
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Profile not found", "statusCode": 404},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )
