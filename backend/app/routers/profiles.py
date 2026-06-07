from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.constants import DEMO_USER_ID
from app.database import get_db
from app.models import User
from app.schemas import UpdateProfile

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/{user_id}")
@router.get("")
def get_profile(user_id: str | None = None, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .options(joinedload(User.profile))
        .filter((User.id == DEMO_USER_ID) | (User.username == "demo"))
        .first()
    )

    if not user or not user.profile:
        return {
            "profile": {
                "displayName": "Alex",
                "avatarId": "detective-default",
                "selfReportedLevel": "beginner",
                "currentLevel": 4,
                "totalXp": 320,
                "onboardingCompleted": False,
            }
        }

    p = user.profile
    return {
        "profile": {
            "id": p.id,
            "userId": p.user_id,
            "avatarId": p.avatar_id,
            "displayName": p.display_name,
            "selfReportedLevel": p.self_reported_level.value,
            "currentLevel": p.current_level,
            "totalXp": p.total_xp,
            "currentLevelXp": p.current_level_xp,
            "dailyStreak": p.daily_streak,
            "onboardingCompleted": p.onboarding_completed,
            "settings": p.settings,
        }
    }


@router.patch("/{user_id}")
def update_profile(body: UpdateProfile, user_id: str = DEMO_USER_ID, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .options(joinedload(User.profile))
        .filter((User.id == DEMO_USER_ID) | (User.username == "demo"))
        .first()
    )

    if not user or not user.profile:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Profile not found", "statusCode": 404})

    profile = user.profile
    if body.displayName is not None:
        profile.display_name = body.displayName
    if body.avatarId is not None:
        profile.avatar_id = body.avatarId
    if body.selfReportedLevel is not None:
        from app.models import SelfReportedLevel
        profile.self_reported_level = SelfReportedLevel(body.selfReportedLevel)
    if body.settings is not None:
        profile.settings = {**profile.settings, **body.settings}

    db.commit()
    db.refresh(profile)

    return {
        "profile": {
            "id": profile.id,
            "displayName": profile.display_name,
            "avatarId": profile.avatar_id,
            "selfReportedLevel": profile.self_reported_level.value,
            "settings": profile.settings,
        }
    }
