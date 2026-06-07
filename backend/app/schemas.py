from typing import Literal

from pydantic import BaseModel, Field


class SubmitFakePostAnswer(BaseModel):
    selectedPostId: Literal["A", "B"]
    hintsUsed: int = Field(default=0, ge=0)
    timeSpentMs: int | None = Field(default=None, ge=0)


class UpdateProfile(BaseModel):
    displayName: str | None = Field(default=None, min_length=1, max_length=50)
    avatarId: str | None = None
    selfReportedLevel: Literal["beginner", "somewhat", "pro"] | None = None
    settings: dict | None = None


class OnboardingComplete(BaseModel):
    level: Literal["beginner", "somewhat", "pro"]
