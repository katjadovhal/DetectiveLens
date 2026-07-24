from typing import Literal

from pydantic import BaseModel, Field


HintStage = Literal[
    "pre_answer_hint",
    "stronger_hint",
    "answer_explanation",
    "detective_tip",
]

PersonalizationMode = Literal["neutral", "skill_practice"]

HintSource = Literal[
    "grounding",
    "curated_fallback",
    "explanation",
    "safe_generic",
    "model",
]


class HintRequest(BaseModel):
    userId: str = Field(..., min_length=1)
    stage: HintStage
    locale: str = Field(default="en", min_length=2, max_length=16)
    # Claims only — never trusted without matching a stored completed attempt.
    attemptNumber: int | None = Field(default=None, ge=1)
    selectedOption: Literal["A", "B"] | None = None
    hintLevel: int | None = Field(default=None, ge=0, le=2)


class HintResponse(BaseModel):
    text: str
    stage: HintStage
    source: HintSource
    personalizationMode: PersonalizationMode
    ageBand: str
    locale: str
