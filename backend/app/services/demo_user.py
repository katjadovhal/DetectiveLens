from sqlalchemy.orm import Session

from app.constants import DEMO_USER_ID
from app.models import Profile, SelfReportedLevel, User


def ensure_demo_user(db: Session) -> User:
    user = db.query(User).filter((User.id == DEMO_USER_ID) | (User.username == "demo")).first()
    if user:
        return user

    user = User(id=DEMO_USER_ID, username="demo", email="demo@detectivelens.local")
    db.add(user)
    db.flush()

    profile = Profile(
        user_id=user.id,
        display_name="Alex",
        self_reported_level=SelfReportedLevel.beginner,
        current_level=4,
        total_xp=320,
        current_level_xp=320,
        onboarding_completed=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user
