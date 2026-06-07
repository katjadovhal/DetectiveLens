from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.constants import DEMO_USER_ID
from app.database import get_db
from app.models import Challenge, SkillScore, User
from app.services.personalization import get_weak_areas

router = APIRouter(prefix="/personalization", tags=["personalization"])


@router.get("/{user_id}/skill-profile")
@router.get("/skill-profile")
def get_skill_profile(user_id: str | None = None, db: Session = Depends(get_db)):
    scores = (
        db.query(SkillScore)
        .options(joinedload(SkillScore.category))
        .join(User)
        .filter((User.id == DEMO_USER_ID) | (User.username == "demo"))
        .all()
    )

    if not scores:
        return {
            "skillProfile": [
                {"categoryId": "source_verification", "score": 45, "attempts": 0, "correct": 0},
                {"categoryId": "content_authenticity", "score": 50, "attempts": 0, "correct": 0},
            ]
        }

    return {
        "skillProfile": [
            {
                "categoryId": s.category_id,
                "score": s.score,
                "attempts": s.attempts,
                "correct": s.correct,
                "categoryName": s.category.name,
            }
            for s in scores
        ]
    }


@router.get("/{user_id}/weak-areas")
@router.get("/weak-areas")
def get_weak_areas_route(user_id: str | None = None, db: Session = Depends(get_db)):
    scores = (
        db.query(SkillScore)
        .join(User)
        .filter((User.id == DEMO_USER_ID) | (User.username == "demo"))
        .all()
    )

    mapped = [
        {"categoryId": s.category_id, "score": s.score, "attempts": s.attempts, "correct": s.correct}
        for s in scores
    ]

    weak = get_weak_areas(mapped) if mapped else [
        {"categoryId": "source_verification", "score": 45, "attempts": 0, "correct": 0}
    ]

    return {"weakAreas": weak}


@router.get("/{user_id}/recommendations")
@router.get("/recommendations")
def get_recommendations(user_id: str | None = None, db: Session = Depends(get_db)):
    challenge = db.query(Challenge).filter(Challenge.slug == "burger-king-001").first()
    return {
        "recommendations": [
            {
                "id": challenge.id if challenge else "burger-king-001",
                "title": "Which post is fake?",
                "type": "fake_post",
                "reason": "Targets your weak area: Source Verification",
            }
        ]
    }
