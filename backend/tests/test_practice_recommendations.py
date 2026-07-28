"""Toy examples for the practice recommendation engine."""

import pytest

from app.repositories import get_next_practice_challenge


USER_ID = "toy-user"


def _challenge(challenge_id: str, skill_id: str, difficulty: str = "medium") -> dict:
    return {
        "id": challenge_id,
        "slug": challenge_id,
        "type": "fake_post",
        "difficulty": difficulty,
        "title": challenge_id,
        "instruction": "Pick the fake post",
        "skillCategoryIds": [skill_id],
        "xpReward": 100,
        "active": True,
        "isDailyEligible": True,
        "content": {"posts": [{"id": "A"}, {"id": "B"}], "correctPostId": "A"},
    }


def _skill_score(skill_id: str, score: float) -> dict:
    return {
        "id": f"{USER_ID}-{skill_id}",
        "userId": USER_ID,
        "categoryId": skill_id,
        "score": score,
        "attempts": 3,
        "correct": 1,
    }


def _completed_attempt(challenge_id: str) -> dict:
    return {
        "id": f"{USER_ID}-{challenge_id}",
        "userId": USER_ID,
        "challengeId": challenge_id,
        "completedAt": "2026-01-01T00:00:00",
        "isCorrect": True,
        "hintsUsed": 0,
    }


def _unfinished_attempt(challenge_id: str) -> dict:
    return {
        "id": f"{USER_ID}-{challenge_id}-unfinished",
        "userId": USER_ID,
        "challengeId": challenge_id,
        "completedAt": None,
        "isCorrect": None,
        "hintsUsed": 0,
    }


def _store(
    *,
    scores: dict[str, float],
    completed: list[str] | None = None,
    unfinished: list[str] | None = None,
) -> dict:
    attempts = [_completed_attempt("warmup-challenge")]
    attempts.extend(_completed_attempt(challenge_id) for challenge_id in completed or [])
    attempts.extend(_unfinished_attempt(challenge_id) for challenge_id in unfinished or [])
    return {
        "skill_scores": [_skill_score(skill_id, score) for skill_id, score in scores.items()],
        "challenge_attempts": attempts,
    }


@pytest.fixture()
def toy_catalogue(monkeypatch):
    challenges = [
        _challenge("challenge-a", "a"),
        _challenge("challenge-b", "b"),
        _challenge("challenge-c", "c"),
        _challenge("challenge-d", "d"),
    ]
    monkeypatch.setattr("app.repositories.get_challenges", lambda: list(challenges))
    return challenges


def test_recommends_challenge_for_weakest_skill(toy_catalogue):
    store = _store(scores={"a": 0.2, "b": -0.9, "c": -0.3, "d": 0.1})

    recommendation = get_next_practice_challenge(USER_ID, store)

    assert recommendation["id"] == "challenge-b"


def test_skips_completed_weakest_challenge_and_recommends_next_best(toy_catalogue):
    store = _store(
        scores={"a": 0.2, "b": -0.9, "c": -0.6, "d": 0.1},
        completed=["challenge-b"],
    )

    recommendation = get_next_practice_challenge(USER_ID, store)

    assert recommendation["id"] == "challenge-c"


def test_completed_challenge_is_not_recommended_even_with_highest_score(toy_catalogue):
    store = _store(
        scores={"a": 0.2, "b": -1.0, "c": 0.1, "d": 0.1},
        completed=["challenge-b"],
    )

    recommendation = get_next_practice_challenge(USER_ID, store)

    assert recommendation["id"] != "challenge-b"


def test_unfinished_challenge_can_be_recommended_again(toy_catalogue):
    store = _store(
        scores={"a": 0.2, "b": -0.9, "c": -0.6, "d": 0.1},
        unfinished=["challenge-b"],
    )

    recommendation = get_next_practice_challenge(USER_ID, store)

    assert recommendation["id"] == "challenge-b"


def test_prefers_better_matching_difficulty_when_skills_are_equally_weak(monkeypatch):
    challenges = [
        _challenge("challenge-hard", "b", difficulty="hard"),
        _challenge("challenge-easy", "c", difficulty="easy"),
    ]
    monkeypatch.setattr("app.repositories.get_challenges", lambda: list(challenges))
    store = _store(scores={"b": -1.0, "c": -1.0})

    recommendation = get_next_practice_challenge(USER_ID, store)

    assert recommendation["id"] == "challenge-easy"


def test_returns_none_after_user_completed_every_challenge(toy_catalogue):
    store = _store(
        scores={"a": -0.1, "b": -0.9, "c": -0.6, "d": 0.0},
        completed=["challenge-a", "challenge-b", "challenge-c", "challenge-d"],
    )

    recommendation = get_next_practice_challenge(USER_ID, store)

    assert recommendation is None
