from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.constants import DEMO_USER_ID, LEVELS
from app.database import get_db
from app.models import Challenge, User

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/{user_id}")
@router.get("")
def get_home(user_id: str | None = None, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .options(joinedload(User.profile))
        .filter((User.id == DEMO_USER_ID) | (User.username == "demo"))
        .first()
    )

    profile = user.profile if user else None
    current_level = profile.current_level if profile else 4
    total_xp = profile.total_xp if profile else 320

    level_info = next((l for l in LEVELS if l["level"] == current_level), LEVELS[3])
    next_level = next((l for l in LEVELS if l["level"] == current_level + 1), None)
    xp_to_next = max(0, (next_level["xp_required"] - total_xp) if next_level else 880)

    daily_challenge = db.query(Challenge).filter(Challenge.slug == "burger-king-001", Challenge.active.is_(True)).first()

    return {
        "greeting": {
            "displayName": profile.display_name if profile else "Alex",
            "levelTitle": level_info["title"],
            "avatarId": profile.avatar_id if profile else "detective-default",
        },
        "progress": {
            "totalXp": total_xp,
            "currentLevelXp": profile.current_level_xp if profile else 320,
            "xpToNextLevel": xp_to_next,
            "level": current_level,
        },
        "dailyMission": {
            "challengeId": daily_challenge.id if daily_challenge else "burger-king-001",
            "title": "Daily Mission!",
            "description": "Spot the fake post",
            "xpBonus": 100,
            "completed": False,
        },
        "continueLearning": {
            "challengeId": (profile.last_challenge_id if profile else None) or (daily_challenge.id if daily_challenge else None),
            "title": daily_challenge.title if daily_challenge else "Which post is fake?",
        },
        "recommendedChallenges": [
            {
                "id": daily_challenge.id if daily_challenge else "burger-king-001",
                "title": "Which post is fake?",
                "type": "fake_post",
                "reason": "Practice source verification",
            }
        ],
    }
