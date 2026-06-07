from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.constants import DEMO_USER_ID
from app.database import get_db
from app.models import Profile, SelfReportedLevel, User
from app.schemas import OnboardingComplete
from app.services.demo_user import ensure_demo_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/welcome")
def get_welcome():
    return {
        "title": "Hey Detective!",
        "subtitle": "The Internet is full of tricks. Let's learn how to spot them.",
        "keyValue": "Become an Internet Detective and learn to spot misinformation and AI-generated content.",
    }


@router.post("/complete")
def complete_onboarding(body: OnboardingComplete, db: Session = Depends(get_db)):
    level = SelfReportedLevel(body.level)

    user = (
        db.query(User)
        .options(joinedload(User.profile))
        .filter((User.id == DEMO_USER_ID) | (User.username == "demo"))
        .first()
    )

    if not user:
        user = User(id=DEMO_USER_ID, username="demo", email="demo@detectivelens.local")
        db.add(user)
        db.flush()
        profile = Profile(user_id=user.id, display_name="Alex", self_reported_level=level, onboarding_completed=True)
        db.add(profile)
    elif user.profile:
        user.profile.self_reported_level = level
        user.profile.onboarding_completed = True
    else:
        profile = Profile(user_id=user.id, display_name="Alex", self_reported_level=level, onboarding_completed=True)
        db.add(profile)

    db.commit()
    return {"success": True, "redirectTo": "/"}
