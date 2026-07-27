"""Deterministic badge engine unit tests."""

from app.badges.engine import evaluate_badge_states, find_newly_unlocked
from app.badges.wording import adapt_badge_message, approved_unlock_message


def _challenge(cid, patterns):
    return {"id": cid, "slug": cid, "skillCategoryIds": patterns}


CHALLENGES = [
    _challenge("c1", ["color"]),  # -> content_authenticity
    _challenge("c2", ["emotions"]),  # -> faces
    _challenge("c3", ["functional"]),  # -> evidence_evaluation
    _challenge("c4", ["blurred_background"]),  # -> backgrounds
    _challenge("c5", ["color", "emotions"]),
]


def _attempt(user_id, challenge_id, *, correct, hints=0, at="2026-01-01T00:00:00", open_=False):
    return {
        "id": f"{challenge_id}-{at}",
        "userId": user_id,
        "challengeId": challenge_id,
        "isCorrect": None if open_ else correct,
        "completedAt": None if open_ else at,
        "hintsUsed": hints,
    }


def test_no_badges_when_no_completed_attempts():
    states = evaluate_badge_states(
        user_id="u1",
        attempts=[_attempt("u1", "c1", correct=True, open_=True)],
        challenges=CHALLENGES,
        user_badges=[],
    )
    assert all(s["status"] == "locked" for s in states)
    assert all(s["progress"] == 0 for s in states)


def test_first_case_unlocks_on_one_completed():
    attempts = [_attempt("u1", "c1", correct=False, at="2026-01-01T01:00:00")]
    newly = find_newly_unlocked(
        user_id="u1",
        attempts=attempts,
        challenges=CHALLENGES,
        user_badges=[],
    )
    ids = {b["id"] for b in newly}
    assert "first_case" in ids
    assert "case_solver" not in ids


def test_case_solver_requires_ten_completed():
    attempts = [
        _attempt("u1", "c1", correct=True, at=f"2026-01-{i+1:02d}T00:00:00")
        for i in range(10)
    ]
    states = evaluate_badge_states(
        user_id="u1",
        attempts=attempts,
        challenges=CHALLENGES,
        user_badges=[],
    )
    solver = next(s for s in states if s["id"] == "case_solver")
    assert solver["status"] == "unlocked"
    assert solver["progress"] == 10


def test_clue_strategist_counts_hint_assisted_correct_only():
    attempts = [
        _attempt("u1", "c1", correct=True, hints=1, at="2026-01-01T00:00:00"),
        _attempt("u1", "c2", correct=True, hints=2, at="2026-01-02T00:00:00"),
        _attempt("u1", "c3", correct=False, hints=3, at="2026-01-03T00:00:00"),
        _attempt("u1", "c4", correct=True, hints=0, at="2026-01-04T00:00:00"),
        _attempt("u1", "c5", correct=True, hints=1, at="2026-01-05T00:00:00"),
    ]
    states = evaluate_badge_states(
        user_id="u1",
        attempts=attempts,
        challenges=CHALLENGES,
        user_badges=[],
    )
    clue = next(s for s in states if s["id"] == "clue_strategist")
    assert clue["progress"] == 3
    assert clue["status"] == "unlocked"


def test_comeback_associated_recovery():
    attempts = [
        _attempt("u1", "c1", correct=False, at="2026-01-01T00:00:00"),  # color miss
        _attempt("u1", "c5", correct=True, at="2026-01-02T00:00:00"),  # color+emotions hit
    ]
    newly = find_newly_unlocked(
        user_id="u1",
        attempts=attempts,
        challenges=CHALLENGES,
        user_badges=[],
    )
    assert any(b["id"] == "comeback_detective" for b in newly)


def test_comeback_requires_later_correct_after_incorrect():
    attempts = [
        _attempt("u1", "c5", correct=True, at="2026-01-01T00:00:00"),
        _attempt("u1", "c1", correct=False, at="2026-01-02T00:00:00"),
    ]
    newly = find_newly_unlocked(
        user_id="u1",
        attempts=attempts,
        challenges=CHALLENGES,
        user_badges=[],
    )
    assert not any(b["id"] == "comeback_detective" for b in newly)


def test_pattern_explorer_needs_four_distinct_skills():
    attempts = [
        _attempt("u1", "c1", correct=True, at="2026-01-01T00:00:00"),
        _attempt("u1", "c2", correct=True, at="2026-01-02T00:00:00"),
        _attempt("u1", "c3", correct=True, at="2026-01-03T00:00:00"),
        _attempt("u1", "c4", correct=True, at="2026-01-04T00:00:00"),
    ]
    states = evaluate_badge_states(
        user_id="u1",
        attempts=attempts,
        challenges=CHALLENGES,
        user_badges=[],
    )
    explorer = next(s for s in states if s["id"] == "pattern_explorer")
    assert explorer["progress"] == 4
    assert explorer["status"] == "unlocked"


def test_detail_detective_recent_accuracy():
    # 5 completed linked to color; 4 of last 5 correct
    attempts = [
        _attempt("u1", "c1", correct=False, at="2026-01-01T00:00:00"),
        _attempt("u1", "c1", correct=True, at="2026-01-02T00:00:00"),
        _attempt("u1", "c5", correct=True, at="2026-01-03T00:00:00"),
        _attempt("u1", "c1", correct=True, at="2026-01-04T00:00:00"),
        _attempt("u1", "c5", correct=True, at="2026-01-05T00:00:00"),
    ]
    newly = find_newly_unlocked(
        user_id="u1",
        attempts=attempts,
        challenges=CHALLENGES,
        user_badges=[],
    )
    assert any(b["id"] == "detail_detective" for b in newly)


def test_no_duplicate_newly_unlocked_when_already_earned():
    attempts = [_attempt("u1", "c1", correct=True, at="2026-01-01T00:00:00")]
    user_badges = [
        {"userId": "u1", "badgeId": "first_case", "earnedAt": "2026-01-01T00:00:00"}
    ]
    newly = find_newly_unlocked(
        user_id="u1",
        attempts=attempts,
        challenges=CHALLENGES,
        user_badges=user_badges,
    )
    assert not any(b["id"] == "first_case" for b in newly)
    states = evaluate_badge_states(
        user_id="u1",
        attempts=attempts,
        challenges=CHALLENGES,
        user_badges=user_badges,
    )
    first = next(s for s in states if s["id"] == "first_case")
    assert first["status"] == "unlocked"
    assert first["earnedAt"] == "2026-01-01T00:00:00"


def test_age_adapted_message_fallback_without_ollama(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "hint_engine_enabled", False)
    text = adapt_badge_message(
        age_band="8_10",
        badge_title="Clue Strategist",
        approved_reason=approved_unlock_message("clue_strategist"),
        context="badge_unlock_notification",
    )
    assert text == "You earned Clue Strategist."
