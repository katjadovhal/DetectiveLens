import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SelfReportedLevel(str, enum.Enum):
    beginner = "beginner"
    somewhat = "somewhat"
    pro = "pro"


class ChallengeType(str, enum.Enum):
    fake_post = "fake_post"
    is_it_real = "is_it_real"
    find_clues = "find_clues"


class Difficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class XpSource(str, enum.Enum):
    challenge = "challenge"
    daily_mission = "daily_mission"
    achievement = "achievement"
    streak_bonus = "streak_bonus"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    username: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped["Profile | None"] = relationship(back_populates="user", uselist=False)
    skill_scores: Mapped[list["SkillScore"]] = relationship(back_populates="user")
    challenge_attempts: Mapped[list["ChallengeAttempt"]] = relationship(back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    avatar_id: Mapped[str] = mapped_column(String(100), default="detective-default")
    display_name: Mapped[str] = mapped_column(String(100))
    self_reported_level: Mapped[SelfReportedLevel] = mapped_column(
        Enum(SelfReportedLevel, name="self_reported_level"), default=SelfReportedLevel.beginner
    )
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    current_level_xp: Mapped[int] = mapped_column(Integer, default=0)
    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    last_challenge_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_challenge_progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    settings: Mapped[dict] = mapped_column(
        JSON, default=lambda: {"notifications": True, "sound": True, "privacy": False}
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class SkillCategory(Base):
    __tablename__ = "skill_categories"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    parent_group: Mapped[str] = mapped_column(String(50))
    library_topic_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    skill_scores: Mapped[list["SkillScore"]] = relationship(back_populates="category")
    challenge_hints: Mapped[list["ChallengeHint"]] = relationship(back_populates="category")


class SkillScore(Base):
    __tablename__ = "skill_scores"
    __table_args__ = (UniqueConstraint("user_id", "category_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[str] = mapped_column(String(50), ForeignKey("skill_categories.id"))
    score: Mapped[float] = mapped_column(Float, default=50.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="skill_scores")
    category: Mapped["SkillCategory"] = relationship(back_populates="skill_scores")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[ChallengeType] = mapped_column(Enum(ChallengeType, name="challenge_type"))
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty, name="difficulty"), default=Difficulty.medium)
    title: Mapped[str] = mapped_column(String(255))
    instruction: Mapped[str] = mapped_column(Text)
    content: Mapped[dict] = mapped_column(JSON)
    skill_category_ids: Mapped[list[str]] = mapped_column(ARRAY(String))
    xp_reward: Mapped[int] = mapped_column(Integer, default=100)
    is_daily_eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    hints: Mapped[list["ChallengeHint"]] = relationship(back_populates="challenge", order_by="ChallengeHint.order")
    attempts: Mapped[list["ChallengeAttempt"]] = relationship(back_populates="challenge")


class ChallengeHint(Base):
    __tablename__ = "challenge_hints"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    challenge_id: Mapped[str] = mapped_column(String(36), ForeignKey("challenges.id", ondelete="CASCADE"))
    order: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(String(255))
    content: Mapped[dict] = mapped_column(JSON)
    skill_category_id: Mapped[str] = mapped_column(String(50), ForeignKey("skill_categories.id"))

    challenge: Mapped["Challenge"] = relationship(back_populates="hints")
    category: Mapped["SkillCategory"] = relationship(back_populates="challenge_hints")


class ChallengeAttempt(Base):
    __tablename__ = "challenge_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    challenge_id: Mapped[str] = mapped_column(String(36), ForeignKey("challenges.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    selected_answer: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    hints_viewed: Mapped[list] = mapped_column(JSON, default=list)
    time_spent_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="challenge_attempts")
    challenge: Mapped["Challenge"] = relationship(back_populates="attempts")


class XpTransaction(Base):
    __tablename__ = "xp_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[int] = mapped_column(Integer)
    source: Mapped[XpSource] = mapped_column(Enum(XpSource, name="xp_source"))
    reference_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Level(Base):
    __tablename__ = "levels"

    level: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    xp_required: Mapped[int] = mapped_column(Integer)


class DetectiveTip(Base):
    __tablename__ = "detective_tips"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    trigger_pattern: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    checklist: Mapped[list] = mapped_column(JSON)


class DailyMission(Base):
    __tablename__ = "daily_missions"
    __table_args__ = (UniqueConstraint("user_id", "date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    date: Mapped[datetime] = mapped_column(Date)
    challenge_id: Mapped[str] = mapped_column(String(36), ForeignKey("challenges.id"))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    xp_bonus: Mapped[int] = mapped_column(Integer, default=100)
