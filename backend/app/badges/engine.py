"""Deterministic Badge Engine — reads completed attempts only; no LLM unlocks."""

from __future__ import annotations

from typing import Any

from app.badges.catalogue import (
    BADGE_CATALOGUE,
    CASE_SOLVER_TARGET,
    CLUE_STRATEGIST_TARGET,
    DETAIL_DETECTIVE_MIN_RELEVANT,
    DETAIL_DETECTIVE_RECENT_CORRECT,
    DETAIL_DETECTIVE_RECENT_WINDOW,
    FIRST_CASE_TARGET,
    PATTERN_EXPLORER_TARGET,
    get_badge_def,
)
from app.constants import canonicalize_skill_ids


def _is_completed(attempt: dict) -> bool:
    return attempt.get("completedAt") is not None and attempt.get("isCorrect") is not None


def completed_attempts_for_user(attempts: list[dict], user_id: str) -> list[dict]:
    completed = [
        a for a in attempts if a.get("userId") == user_id and _is_completed(a)
    ]
    completed.sort(key=lambda a: a.get("completedAt") or "")
    return completed


def _challenge_patterns(challenge: dict | None) -> list[str]:
    if not challenge:
        return []
    return canonicalize_skill_ids(challenge.get("skillCategoryIds") or [])


def _earned_map(user_badges: list[dict], user_id: str) -> dict[str, str]:
    return {
        row["badgeId"]: row.get("earnedAt")
        for row in user_badges
        if row.get("userId") == user_id and row.get("badgeId")
    }


def _progress_first_case(completed: list[dict]) -> tuple[int, int, bool]:
    count = len(completed)
    return min(count, FIRST_CASE_TARGET), FIRST_CASE_TARGET, count >= FIRST_CASE_TARGET


def _progress_case_solver(completed: list[dict]) -> tuple[int, int, bool]:
    count = len(completed)
    return min(count, CASE_SOLVER_TARGET), CASE_SOLVER_TARGET, count >= CASE_SOLVER_TARGET


def _progress_clue_strategist(completed: list[dict]) -> tuple[int, int, bool]:
    count = sum(
        1
        for a in completed
        if a.get("isCorrect") is True and int(a.get("hintsUsed") or 0) > 0
    )
    return (
        min(count, CLUE_STRATEGIST_TARGET),
        CLUE_STRATEGIST_TARGET,
        count >= CLUE_STRATEGIST_TARGET,
    )


def _progress_comeback(
    completed: list[dict],
    challenges_by_id: dict[str, dict],
) -> tuple[int, int, bool]:
    """Associated recovery: earlier incorrect and later correct sharing a pattern."""
    first_incorrect_at: dict[str, str] = {}
    for attempt in completed:
        challenge = challenges_by_id.get(attempt.get("challengeId"))
        patterns = _challenge_patterns(challenge)
        completed_at = attempt.get("completedAt") or ""
        if attempt.get("isCorrect") is False:
            for pattern in patterns:
                if pattern not in first_incorrect_at:
                    first_incorrect_at[pattern] = completed_at

    for attempt in completed:
        if attempt.get("isCorrect") is not True:
            continue
        completed_at = attempt.get("completedAt") or ""
        challenge = challenges_by_id.get(attempt.get("challengeId"))
        for pattern in _challenge_patterns(challenge):
            earlier = first_incorrect_at.get(pattern)
            if earlier and earlier < completed_at:
                return 1, 1, True
    return 0, 1, False


def _progress_pattern_explorer(
    completed: list[dict],
    challenges_by_id: dict[str, dict],
) -> tuple[int, int, bool]:
    patterns: set[str] = set()
    for attempt in completed:
        challenge = challenges_by_id.get(attempt.get("challengeId"))
        patterns.update(_challenge_patterns(challenge))
    count = len(patterns)
    return (
        min(count, PATTERN_EXPLORER_TARGET),
        PATTERN_EXPLORER_TARGET,
        count >= PATTERN_EXPLORER_TARGET,
    )


def _progress_detail_detective(
    completed: list[dict],
    challenges_by_id: dict[str, dict],
) -> tuple[int, int, bool]:
    by_pattern: dict[str, list[dict]] = {}
    for attempt in completed:
        challenge = challenges_by_id.get(attempt.get("challengeId"))
        for pattern in _challenge_patterns(challenge):
            by_pattern.setdefault(pattern, []).append(attempt)

    best_progress = 0
    unlocked = False
    for attempts in by_pattern.values():
        relevant = sorted(attempts, key=lambda a: a.get("completedAt") or "")
        relevant_count = len(relevant)
        best_progress = max(best_progress, min(relevant_count, DETAIL_DETECTIVE_MIN_RELEVANT))
        if relevant_count < DETAIL_DETECTIVE_MIN_RELEVANT:
            continue
        recent = relevant[-DETAIL_DETECTIVE_RECENT_WINDOW:]
        recent_correct = sum(1 for a in recent if a.get("isCorrect") is True)
        if recent_correct >= DETAIL_DETECTIVE_RECENT_CORRECT:
            unlocked = True
            best_progress = DETAIL_DETECTIVE_MIN_RELEVANT
            break

    return best_progress, DETAIL_DETECTIVE_MIN_RELEVANT, unlocked


_PROGRESS_FNS = {
    "first_case": lambda c, _: _progress_first_case(c),
    "case_solver": lambda c, _: _progress_case_solver(c),
    "clue_strategist": lambda c, _: _progress_clue_strategist(c),
    "comeback_detective": _progress_comeback,
    "pattern_explorer": _progress_pattern_explorer,
    "detail_detective": _progress_detail_detective,
}


def evaluate_badge_states(
    *,
    user_id: str,
    attempts: list[dict],
    challenges: list[dict],
    user_badges: list[dict],
) -> list[dict[str, Any]]:
    completed = completed_attempts_for_user(attempts, user_id)
    challenges_by_id = {c["id"]: c for c in challenges}
    # Also index by slug for older attempt rows that may store slug ids.
    for challenge in challenges:
        slug = challenge.get("slug")
        if slug:
            challenges_by_id.setdefault(slug, challenge)

    earned = _earned_map(user_badges, user_id)
    results: list[dict[str, Any]] = []

    for badge in BADGE_CATALOGUE:
        badge_id = badge["id"]
        progress_fn = _PROGRESS_FNS[badge_id]
        progress, target, qualifies = progress_fn(completed, challenges_by_id)
        already = badge_id in earned
        unlocked = already or qualifies
        results.append(
            {
                "id": badge_id,
                "title": badge["title"],
                "description": badge["description"],
                "icon": badge["icon"],
                "category": badge["category"],
                "status": "unlocked" if unlocked else "locked",
                "progress": target if already else progress,
                "target": target,
                "earnedAt": earned.get(badge_id),
                "whyItMatters": badge["whyItMatters"],
            }
        )
    return results


def find_newly_unlocked(
    *,
    user_id: str,
    attempts: list[dict],
    challenges: list[dict],
    user_badges: list[dict],
) -> list[dict[str, Any]]:
    """Return catalogue entries that newly qualify and are not yet persisted."""
    states = evaluate_badge_states(
        user_id=user_id,
        attempts=attempts,
        challenges=challenges,
        user_badges=user_badges,
    )
    earned = _earned_map(user_badges, user_id)
    newly: list[dict[str, Any]] = []
    for state in states:
        if state["status"] == "unlocked" and state["id"] not in earned:
            definition = get_badge_def(state["id"])
            if definition:
                newly.append({**definition, **state})
    return newly
