"""Deterministic interaction analytics from completed challenge attempts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import median
from typing import Any

RECENT_WINDOW = 4
MIN_RELEVANT_ATTEMPTS = 3
REPEATED_MISS_MIN_INCORRECT = 2
DEVELOPING_STRENGTH_ACCURACY = 0.75
MIN_TIME_SAMPLES = 3
STRONGER_HINT_SUFFIX = ":stronger_hint:v1"


@dataclass
class PatternInteractionSummary:
    pattern_id: str
    relevant_attempts: int = 0
    correct: int = 0
    incorrect: int = 0
    accuracy: float = 0.0
    recent_correct: int = 0
    recent_incorrect: int = 0
    hint_assisted_correct: int = 0
    independent_correct: int = 0
    stronger_hints_used: int = 0
    recent_recovery: bool = False
    repeated_associated_miss: bool = False
    valid_time_samples: int = 0
    median_time_spent_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "patternId": self.pattern_id,
            "relevantAttempts": self.relevant_attempts,
            "correct": self.correct,
            "incorrect": self.incorrect,
            "accuracy": self.accuracy,
            "recentCorrect": self.recent_correct,
            "recentIncorrect": self.recent_incorrect,
            "hintAssistedCorrect": self.hint_assisted_correct,
            "independentCorrect": self.independent_correct,
            "strongerHintsUsed": self.stronger_hints_used,
            "recentRecovery": self.recent_recovery,
            "repeatedAssociatedMiss": self.repeated_associated_miss,
            "validTimeSamples": self.valid_time_samples,
            "medianTimeSpentMs": self.median_time_spent_ms,
        }


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _is_completed(attempt: dict) -> bool:
    return attempt.get("completedAt") is not None and attempt.get("isCorrect") is not None


def _attempt_time_ms(attempt: dict) -> int | None:
    explicit = attempt.get("timeSpentMs")
    if isinstance(explicit, int) and explicit >= 0:
        return explicit
    started = _parse_iso(attempt.get("startedAt"))
    completed = _parse_iso(attempt.get("completedAt"))
    if started and completed:
        delta = int((completed - started).total_seconds() * 1000)
        return delta if delta >= 0 else None
    return None


def _stronger_hint_used(attempt: dict) -> bool:
    viewed = attempt.get("hintsViewed") or []
    return any(str(h).endswith(STRONGER_HINT_SUFFIX) for h in viewed)


def build_pattern_summaries(
    user_id: str,
    attempts: list[dict],
    challenges_by_id: dict[str, dict],
    pattern_ids: list[str] | None = None,
) -> dict[str, PatternInteractionSummary]:
    completed = [
        a for a in attempts
        if a.get("userId") == user_id and _is_completed(a)
    ]
    completed.sort(key=lambda a: a.get("completedAt") or "")

    all_patterns: set[str] = set(pattern_ids or [])
    for attempt in completed:
        challenge = challenges_by_id.get(attempt.get("challengeId"))
        if challenge:
            all_patterns.update(challenge.get("skillCategoryIds") or [])

    summaries: dict[str, PatternInteractionSummary] = {}
    for pattern_id in sorted(all_patterns):
        relevant: list[dict] = []
        for attempt in completed:
            challenge = challenges_by_id.get(attempt.get("challengeId"))
            if not challenge:
                continue
            if pattern_id in (challenge.get("skillCategoryIds") or []):
                relevant.append(attempt)

        summary = PatternInteractionSummary(pattern_id=pattern_id)
        summary.relevant_attempts = len(relevant)
        if not relevant:
            summaries[pattern_id] = summary
            continue

        for attempt in relevant:
            if attempt.get("isCorrect"):
                summary.correct += 1
                hints_used = int(attempt.get("hintsUsed") or 0)
                if hints_used > 0:
                    summary.hint_assisted_correct += 1
                else:
                    summary.independent_correct += 1
            else:
                summary.incorrect += 1
            if _stronger_hint_used(attempt):
                summary.stronger_hints_used += 1

        summary.accuracy = summary.correct / summary.relevant_attempts

        recent = relevant[-RECENT_WINDOW:]
        summary.recent_correct = sum(1 for a in recent if a.get("isCorrect"))
        summary.recent_incorrect = sum(1 for a in recent if not a.get("isCorrect"))

        if summary.relevant_attempts >= MIN_RELEVANT_ATTEMPTS:
            if summary.recent_incorrect >= REPEATED_MISS_MIN_INCORRECT:
                summary.repeated_associated_miss = True

        # Recovery: earlier incorrect then later correct in relevant sequence
        saw_incorrect = False
        for attempt in relevant:
            if not attempt.get("isCorrect"):
                saw_incorrect = True
            elif saw_incorrect and attempt.get("isCorrect"):
                summary.recent_recovery = True
                break

        times = [t for t in (_attempt_time_ms(a) for a in relevant) if t is not None]
        summary.valid_time_samples = len(times)
        if len(times) >= MIN_TIME_SAMPLES:
            summary.median_time_spent_ms = int(median(times))

        summaries[pattern_id] = summary

    return summaries


def compact_summary_for_patterns(
    summaries: dict[str, PatternInteractionSummary],
    pattern_ids: list[str],
) -> dict[str, Any]:
    """Small payload for LLM — facts only, no raw attempts."""
    items = []
    for pid in pattern_ids:
        s = summaries.get(pid)
        if not s or s.relevant_attempts == 0:
            continue
        items.append(s.to_dict())
    total_relevant = sum(s.relevant_attempts for s in summaries.values())
    return {
        "patterns": items,
        "totalRelevantAttempts": total_relevant,
    }
