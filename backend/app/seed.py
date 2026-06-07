import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.constants import DEMO_USER_ID, LEVELS, SKILL_CATEGORIES
from app.database import Base, engine, SessionLocal
from app.models import (
    Challenge,
    ChallengeHint,
    ChallengeType,
    DetectiveTip,
    Difficulty,
    Level,
    Profile,
    SelfReportedLevel,
    SkillCategory,
    User,
)

CHALLENGE_DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "challenge-data"


def seed(db: Session) -> None:
    for category in SKILL_CATEGORIES:
        existing = db.get(SkillCategory, category["id"])
        if existing:
            existing.name = category["name"]
            existing.parent_group = category["parent_group"]
            existing.library_topic_id = category["library_topic_id"]
        else:
            db.add(SkillCategory(**category))

    for level in LEVELS:
        existing = db.get(Level, level["level"])
        if existing:
            existing.title = level["title"]
            existing.xp_required = level["xp_required"]
        else:
            db.add(Level(level=level["level"], title=level["title"], xp_required=level["xp_required"]))

    burger_path = CHALLENGE_DATA_ROOT / "fake-post" / "burger-king-001.json"
    burger_king = json.loads(burger_path.read_text())

    challenge = db.query(Challenge).filter(Challenge.slug == burger_king["slug"]).first()
    if challenge:
        challenge.type = ChallengeType(burger_king["type"])
        challenge.difficulty = Difficulty(burger_king["difficulty"])
        challenge.title = burger_king["title"]
        challenge.instruction = burger_king["instruction"]
        challenge.content = burger_king["content"]
        challenge.skill_category_ids = burger_king["skillCategoryIds"]
        challenge.xp_reward = burger_king["xpReward"]
    else:
        challenge = Challenge(
            slug=burger_king["slug"],
            type=ChallengeType(burger_king["type"]),
            difficulty=Difficulty(burger_king["difficulty"]),
            title=burger_king["title"],
            instruction=burger_king["instruction"],
            content=burger_king["content"],
            skill_category_ids=burger_king["skillCategoryIds"],
            xp_reward=burger_king["xpReward"],
            is_daily_eligible=True,
        )
        db.add(challenge)
        db.flush()

    for hint_data in burger_king["hints"]:
        hint = db.get(ChallengeHint, hint_data["id"])
        if hint:
            hint.challenge_id = challenge.id
            hint.order = hint_data["order"]
            hint.question = hint_data["question"]
            hint.content = hint_data["content"]
            hint.skill_category_id = hint_data["skillCategoryId"]
        else:
            db.add(
                ChallengeHint(
                    id=hint_data["id"],
                    challenge_id=challenge.id,
                    order=hint_data["order"],
                    question=hint_data["question"],
                    content=hint_data["content"],
                    skill_category_id=hint_data["skillCategoryId"],
                )
            )

    tip = db.get(DetectiveTip, "trusts_familiar_brands")
    if not tip:
        db.add(
            DetectiveTip(
                id="trusts_familiar_brands",
                trigger_pattern="wrong_on_fake_post_trusting_verified",
                message=(
                    "You often trust posts from familiar brands without checking whether "
                    "the content matches what they normally share."
                ),
                checklist=[
                    "Check if the message fits the source",
                    "Look for unusual or surprising claims",
                    "Ask whether the post supports the account's goals",
                ],
            )
        )

    user = db.get(User, DEMO_USER_ID)
    if not user:
        user = User(id=DEMO_USER_ID, username="demo", email="demo@detectivelens.local")
        db.add(user)
        db.flush()
        db.add(
            Profile(
                user_id=user.id,
                display_name="Alex",
                self_reported_level=SelfReportedLevel.beginner,
                current_level=4,
                total_xp=320,
                current_level_xp=320,
                onboarding_completed=True,
            )
        )

    db.commit()
    print("Seed completed.")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
