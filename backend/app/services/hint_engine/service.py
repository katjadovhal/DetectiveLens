"""Age-adaptive hint engine orchestration."""

from __future__ import annotations

import logging
from typing import Any

from app.schemas import HintResponse
from app.services.hint_engine.analytics import build_pattern_summaries, compact_summary_for_patterns
from app.services.hint_engine.deterministic import (
    build_answer_explanation,
    build_detective_tip,
    build_pre_answer_hint,
)
from app.services.hint_engine.ollama_adapter import adapt_with_ollama
from app.services.hint_engine.policy import select_personalization_mode, select_practice_challenge
from app.services.hint_engine.validation import to_adaptive_message, validate_message
from app.storage import load_store

logger = logging.getLogger(__name__)

DEFAULT_AGE_BAND = "11_13"
HINT_VERSION = "v1"


def derive_age_band(age: int) -> str:
    if age <= 10:
        return "8_10"
    if age <= 13:
        return "11_13"
    return "14_16"


def stable_hint_id(slug: str, stage: str) -> str:
    return f"{slug}:{stage}:{HINT_VERSION}"


def _challenges_by_id(challenges: list[dict]) -> dict[str, dict]:
    return {c["id"]: c for c in challenges}


def _find_completed_attempt(attempts: list[dict], user_id: str, challenge_id: str) -> dict | None:
    completed = [
        a for a in attempts
        if a.get("userId") == user_id
        and a.get("challengeId") == challenge_id
        and a.get("completedAt")
        and a.get("isCorrect") is not None
    ]
    if not completed:
        return None
    return max(completed, key=lambda a: a.get("completedAt") or "")


def _find_open_attempt(attempts: list[dict], session_id: str | None, user_id: str, challenge_id: str) -> dict | None:
    if session_id:
        attempt = next((a for a in attempts if a.get("id") == session_id), None)
        if attempt and not attempt.get("completedAt") and attempt.get("userId") == user_id:
            return attempt
    for attempt in reversed(attempts):
        if (
            attempt.get("userId") == user_id
            and attempt.get("challengeId") == challenge_id
            and not attempt.get("completedAt")
        ):
            return attempt
    return None


def build_detective_tip_payload(
    pattern_ids: list[str],
    summaries: dict,
    policy,
) -> dict:
    return build_detective_tip(pattern_ids, policy.personalization_mode, policy.evidence_count)


async def generate_hint(
    challenge: dict,
    *,
    user_id: str,
    stage: str,
    session_id: str | None,
    locale: str,
    challenges: list[dict],
    profile: dict | None,
    record_hint_view_fn=None,
) -> HintResponse:
    store = load_store()
    attempts = store.get("challenge_attempts", [])
    pattern_ids = list(challenge.get("skillCategoryIds") or [])
    slug = challenge.get("slug") or challenge["id"]
    age_band = (profile or {}).get("ageBand") or DEFAULT_AGE_BAND
    is_young = bool((profile or {}).get("youngReader"))

    summaries = build_pattern_summaries(
        user_id,
        attempts,
        _challenges_by_id(challenges),
        pattern_ids,
    )
    policy = select_personalization_mode(summaries, pattern_ids)
    interaction_summary = compact_summary_for_patterns(summaries, pattern_ids)

    fallback_used = False
    recommended_challenge_id = None

    if stage in ("pre_answer_hint", "stronger_hint"):
        open_attempt = _find_open_attempt(attempts, session_id, user_id, challenge["id"])
        if not open_attempt:
            raise ValueError("No active challenge session")

        pre_id = stable_hint_id(slug, "pre_answer_hint")
        strong_id = stable_hint_id(slug, "stronger_hint")
        viewed = list(open_attempt.get("hintsViewed") or [])

        if stage == "stronger_hint" and pre_id not in viewed:
            raise ValueError("Request the first clue before a stronger clue")
        if stage == "stronger_hint" and strong_id in viewed:
            raise ValueError("Stronger clue already used")

        approved = build_pre_answer_hint(pattern_ids, stage)
        for unknown in approved.get("unknown_pattern_ids") or []:
            logger.info("Unknown pattern id in hint request: %s", unknown)

        message = to_adaptive_message(approved)
        adapted = await adapt_with_ollama(
            age_band=age_band,
            locale=locale,
            stage=stage,
            approved=approved,
            pattern_ids=approved["pattern_ids"],
            personalization_mode=policy.personalization_mode,
            interaction_summary=interaction_summary,
        )
        if adapted:
            errors = validate_message(
                adapted,
                stage=stage,
                allowed_pattern_ids=pattern_ids,
                age_band=age_band,
                is_young=is_young,
                approved_text=approved["text"],
            )
            if not errors:
                message = adapted
            else:
                fallback_used = True
                logger.info("Hint validation failed: %s", errors)
        else:
            fallback_used = True

        hint_id = pre_id if stage == "pre_answer_hint" else strong_id
        if record_hint_view_fn and hint_id not in viewed:
            record_hint_view_fn(open_attempt["id"], hint_id)

    else:
        completed = _find_completed_attempt(attempts, user_id, challenge["id"])
        if not completed:
            raise ValueError("Completed attempt required")

        content = challenge.get("content") or {}
        bullets = (content.get("explanation") or {}).get("bullets") or []

        if stage == "answer_explanation":
            approved = build_answer_explanation(bullets)
        else:
            approved = build_detective_tip(
                pattern_ids,
                policy.personalization_mode,
                policy.evidence_count,
            )
            recommended_challenge_id = select_practice_challenge(
                user_id,
                challenge["id"],
                policy.practice_pattern,
                attempts,
                challenges,
                challenge.get("difficulty", "medium"),
            )

        for unknown in approved.get("unknown_pattern_ids") or []:
            logger.info("Unknown pattern id in post-answer hint: %s", unknown)

        message = to_adaptive_message(approved)
        adapted = await adapt_with_ollama(
            age_band=age_band,
            locale=locale,
            stage=stage,
            approved=approved,
            pattern_ids=approved["pattern_ids"],
            personalization_mode=policy.personalization_mode,
            interaction_summary=interaction_summary,
        )
        if adapted:
            errors = validate_message(
                adapted,
                stage=stage,
                allowed_pattern_ids=pattern_ids,
                age_band=age_band,
                is_young=is_young,
                approved_text=approved["text"],
            )
            if not errors:
                message = adapted
            else:
                fallback_used = True
        else:
            fallback_used = True

    return HintResponse(
        title=message.title,
        text=message.text,
        checklist=message.checklist,
        tone=message.tone,
        patternIds=message.pattern_ids,
        personalizationMode=policy.personalization_mode,
        evidenceClaim=message.evidence_claim,
        revealsAnswer=message.reveals_answer,
        fallbackUsed=fallback_used,
        recommendedChallengeId=recommended_challenge_id,
        ageBand=age_band,
    )


def get_learning_insights(
    user_id: str,
    challenges: list[dict],
) -> dict[str, Any]:
    store = load_store()
    attempts = store.get("challenge_attempts", [])
    by_id = _challenges_by_id(challenges)
    summaries = build_pattern_summaries(user_id, attempts, by_id)
    all_patterns = list(summaries.keys())
    policy = select_personalization_mode(summaries, all_patterns)

    practice_pattern = policy.practice_pattern
    recommended = None
    if practice_pattern:
        recommended = select_practice_challenge(
            user_id,
            "",
            practice_pattern,
            attempts,
            challenges,
            "medium",
        )

    developing = None
    for pid, summary in summaries.items():
        if summary.relevant_attempts >= 3 and summary.accuracy >= 0.75:
            developing = pid
            break

    recovery = any(s.recent_recovery for s in summaries.values())

    status = "ready" if any(s.relevant_attempts > 0 for s in summaries.values()) else "insufficient_data"

    return {
        "status": status,
        "patterns": [s.to_dict() for s in summaries.values() if s.relevant_attempts > 0],
        "practicePattern": practice_pattern,
        "developingStrength": developing,
        "recentRecovery": recovery,
        "recommendedChallengeIds": [recommended] if recommended else [],
        "personalizationMode": policy.personalization_mode,
        "message": None,
    }
