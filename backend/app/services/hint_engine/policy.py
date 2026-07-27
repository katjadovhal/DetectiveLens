"""Deterministic pedagogical policy — modes and practice recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.services.hint_engine.analytics import (
    MIN_RELEVANT_ATTEMPTS,
    PatternInteractionSummary,
    RECENT_WINDOW,
    DEVELOPING_STRENGTH_ACCURACY,
)

DIFFICULTY_RANK = {"easy": 0, "medium": 1, "hard": 2}
RECENT_COMPLETION_HOURS = 24


@dataclass
class PolicyResult:
    personalization_mode: str
    practice_pattern: str | None = None
    recommended_challenge_id: str | None = None
    evidence_count: int | None = None


def select_personalization_mode(
    summaries: dict[str, PatternInteractionSummary],
    focus_pattern_ids: list[str],
) -> PolicyResult:
    focus = [summaries[p] for p in focus_pattern_ids if p in summaries]
    if not focus:
        return PolicyResult(personalization_mode="insufficient_data")

    total_relevant = sum(s.relevant_attempts for s in focus)
    if total_relevant < MIN_RELEVANT_ATTEMPTS:
        return PolicyResult(
            personalization_mode="insufficient_data",
            evidence_count=total_relevant,
        )

    recent_recovery = any(s.recent_recovery for s in focus)
    practice_support = any(s.repeated_associated_miss for s in focus)
    hint_scaffolding = any(
        s.hint_assisted_correct >= 1 and s.relevant_attempts >= MIN_RELEVANT_ATTEMPTS
        for s in focus
    )
    developing_strength = any(
        s.relevant_attempts >= MIN_RELEVANT_ATTEMPTS
        and s.accuracy >= DEVELOPING_STRENGTH_ACCURACY
        for s in focus
    )

    if recent_recovery:
        mode = "recent_recovery"
    elif practice_support:
        mode = "practice_support"
    elif hint_scaffolding:
        mode = "hint_scaffolding"
    elif developing_strength:
        mode = "developing_strength"
    else:
        mode = "neutral"

    practice_pattern = None
    if practice_support:
        worst = max(
            focus,
            key=lambda s: (s.repeated_associated_miss, s.incorrect, -s.accuracy),
        )
        practice_pattern = worst.pattern_id

    return PolicyResult(
        personalization_mode=mode,
        practice_pattern=practice_pattern,
        evidence_count=min(total_relevant, RECENT_WINDOW),
    )


def select_practice_challenge(
    user_id: str,
    current_challenge_id: str,
    pattern_id: str | None,
    attempts: list[dict],
    challenges: list[dict],
    current_difficulty: str,
) -> str | None:
    if not pattern_id:
        return None

    now = datetime.utcnow()
    recent_cutoff = now - timedelta(hours=RECENT_COMPLETION_HOURS)
    recent_ids: set[str] = set()
    for attempt in attempts:
        if attempt.get("userId") != user_id or not attempt.get("completedAt"):
            continue
        completed = attempt.get("completedAt")
        try:
            if datetime.fromisoformat(completed) >= recent_cutoff:
                recent_ids.add(attempt.get("challengeId"))
        except (TypeError, ValueError):
            continue

    current_rank = DIFFICULTY_RANK.get(str(current_difficulty).lower(), 1)

    candidates = []
    for challenge in challenges:
        cid = challenge["id"]
        if cid == current_challenge_id:
            continue
        if cid in recent_ids:
            continue
        if pattern_id not in (challenge.get("skillCategoryIds") or []):
            continue
        diff_rank = DIFFICULTY_RANK.get(str(challenge.get("difficulty", "medium")).lower(), 1)
        if diff_rank > current_rank:
            continue
        candidates.append(challenge)

    if not candidates:
        return None

    # Prefer easier, then equal difficulty
    candidates.sort(
        key=lambda c: (
            DIFFICULTY_RANK.get(str(c.get("difficulty", "medium")).lower(), 1),
            c.get("id"),
        ),
    )
    return candidates[0]["id"]
