"""Validate adaptive messages and enforce safety rules."""

from __future__ import annotations

import re

from app.schemas import AdaptiveMessage, MessagePresentation
from app.services.hint_engine.pattern_templates import WORD_LIMITS, YOUNG_WORD_LIMIT
from app.services.hint_engine.presentation import default_presentation, validate_presentation

FORBIDDEN_PHRASES = [
    "you are bad at",
    "you always",
    "you always miss",
    "you often trust",
    "you depend on hints",
    "you cannot solve this alone",
    "you have confirmation bias",
    "you are careless",
    "you failed to notice",
    "cognitive error",
    "confirmation bias",
]

PRE_ANSWER_FORBIDDEN = [
    "correct answer",
    "real photograph",
    "ai-generated",
    "ai generated",
    "fake image",
    "option a",
    "option b",
    "image a is",
    "image b is",
    "choose a",
    "choose b",
    "pick a",
    "pick b",
]

OPTION_LABEL_RE = re.compile(r"(?<![a-z])option\s+[ab](?![a-z])", re.I)
UNSAFE_MARKUP_RE = re.compile(
    r"(</?[a-z][^>]*>|javascript:|url\(|@font-face|font-family\s*:)",
    re.I,
)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


def validate_message(
    message: AdaptiveMessage,
    *,
    stage: str,
    allowed_pattern_ids: list[str],
    age_band: str,
    is_young: bool = False,
    approved_text: str | None = None,
) -> list[str]:
    errors: list[str] = []

    limit = YOUNG_WORD_LIMIT if is_young else WORD_LIMITS.get(age_band, WORD_LIMITS["11_13"])
    if _word_count(message.text) > limit:
        errors.append("word_limit_exceeded")

    combined = f"{message.text} {' '.join(message.checklist)}".lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in combined:
            errors.append(f"forbidden_phrase:{phrase}")

    if UNSAFE_MARKUP_RE.search(f"{message.title} {message.text} {' '.join(message.checklist)}"):
        errors.append("unsafe_markup")

    for pid in message.pattern_ids:
        if pid not in allowed_pattern_ids:
            errors.append(f"unknown_pattern:{pid}")

    if len(message.checklist) > 3:
        errors.append("checklist_too_long")

    if stage in ("pre_answer_hint", "stronger_hint"):
        if message.reveals_answer:
            errors.append("reveals_answer")
        for phrase in PRE_ANSWER_FORBIDDEN:
            if phrase in combined:
                errors.append(f"pre_answer_forbidden:{phrase}")
        if OPTION_LABEL_RE.search(combined):
            errors.append("option_reference")

    if message.evidence_claim:
        if not re.fullmatch(r"\d+", message.evidence_claim.strip()):
            errors.append("invalid_evidence_claim")

    if approved_text and stage in ("answer_explanation", "detective_tip"):
        numbers = re.findall(r"\b\d+\b", message.text)
        approved_numbers = re.findall(r"\b\d+\b", approved_text)
        for num in numbers:
            if num not in approved_numbers and "last" in message.text.lower():
                errors.append("invented_count")

    errors.extend(validate_presentation(message.presentation, age_band))
    return errors


def to_adaptive_message(payload: dict, age_band: str) -> AdaptiveMessage:
    presentation = payload.get("presentation")
    if isinstance(presentation, MessagePresentation):
        resolved = presentation
    elif isinstance(presentation, dict):
        resolved = MessagePresentation.model_validate(presentation)
    else:
        resolved = default_presentation(age_band)

    return AdaptiveMessage(
        title=payload["title"],
        text=payload["text"],
        checklist=payload.get("checklist") or [],
        tone=payload.get("tone", "supportive"),
        pattern_ids=payload.get("pattern_ids") or [],
        evidence_claim=payload.get("evidence_claim"),
        reveals_answer=bool(payload.get("reveals_answer")),
        presentation=resolved,
    )
