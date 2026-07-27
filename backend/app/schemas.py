from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SubmitFakePostAnswer(BaseModel):
    selectedPostId: Literal["A", "B"]
    hintsUsed: int = Field(default=0, ge=0)
    timeSpentMs: int | None = Field(default=None, ge=0)


class UpdateProfile(BaseModel):
    displayName: str | None = Field(default=None, min_length=1, max_length=50)
    avatarId: str | None = None
    settings: dict | None = None


class PurchaseHqItem(BaseModel):
    itemId: str = Field(..., min_length=1, max_length=64)


class CreateUser(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=5, le=99)
    colorBlindness: bool = False
    avatarId: str


class OnboardingComplete(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=5, le=99)
    colorBlindness: bool = False
    avatarId: str


class MessagePresentation(BaseModel):
    preset: Literal["young_reader", "middle_reader", "advanced_reader"]
    font_style: Literal["rounded", "standard"]
    font_scale: Literal["large", "medium", "compact"]
    line_spacing: Literal["relaxed", "normal"]
    content_width: Literal["narrow", "medium", "wide"]
    emphasis_style: Literal["keywords", "none"]


class AdaptiveMessage(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    text: str = Field(min_length=1, max_length=500)
    checklist: list[str] = Field(default_factory=list, max_length=3)
    tone: Literal["neutral", "supportive", "encouraging"]
    pattern_ids: list[str] = Field(default_factory=list)
    evidence_claim: str | None = None
    reveals_answer: bool = False
    presentation: MessagePresentation

    @field_validator("checklist")
    @classmethod
    def limit_checklist(cls, value: list[str]) -> list[str]:
        return value[:3]


class HintRequest(BaseModel):
    userId: str = Field(min_length=1, max_length=64)
    sessionId: str | None = Field(default=None, max_length=64)
    stage: Literal[
        "pre_answer_hint",
        "stronger_hint",
        "answer_explanation",
        "detective_tip",
        "practice_recommendation",
    ]
    locale: str = Field(default="en", max_length=16)


class HintResponse(BaseModel):
    title: str
    text: str
    checklist: list[str] = Field(default_factory=list)
    tone: str
    patternIds: list[str] = Field(default_factory=list)
    personalizationMode: str
    evidenceClaim: str | None = None
    revealsAnswer: bool = False
    fallbackUsed: bool = False
    recommendedChallengeId: str | None = None
    ageBand: str | None = None
    presentation: MessagePresentation | None = None
    practiceRecommendation: dict | None = None
