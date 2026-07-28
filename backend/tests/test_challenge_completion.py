"""All-challenges-completed derivation and API guards."""

import json

import pytest
from fastapi.testclient import TestClient

from app.repositories import (
    ALL_CHALLENGES_COMPLETED_NEXT_ROUTE,
    ALL_CHALLENGES_COMPLETED_STATUS,
    compute_challenge_completion,
    get_next_practice_challenge,
)


def _challenge(cid):
    return {
        "id": cid,
        "slug": cid,
        "type": "fake_post",
        "difficulty": "beginner",
        "title": cid,
        "instruction": "Pick the fake post",
        "skillCategoryIds": ["color"],
        "xpReward": 100,
        "active": True,
        "isDailyEligible": True,
        "content": {"posts": [{"id": "A"}, {"id": "B"}], "correctPostId": "A"},
    }


def _attempt(user_id, challenge_id, *, completed=True, at="2026-01-01T00:00:00"):
    return {
        "id": f"{user_id}-{challenge_id}-{at}",
        "userId": user_id,
        "challengeId": challenge_id,
        "completedAt": at if completed else None,
        "isCorrect": True if completed else None,
        "hintsUsed": 0,
    }


@pytest.fixture()
def catalogue(monkeypatch):
    challenges = [_challenge("busDriver-001"), _challenge("library-001"), _challenge("classroom-001")]

    def fake_get_challenges():
        return list(challenges)

    monkeypatch.setattr("app.repositories.get_challenges", fake_get_challenges)
    return challenges


def test_empty_catalogue_is_not_completed(monkeypatch):
    monkeypatch.setattr("app.repositories.get_challenges", lambda: [])
    result = compute_challenge_completion("u1", {"challenge_attempts": []})
    assert result == {
        "allChallengesCompleted": False,
        "completedChallenges": 0,
        "totalChallenges": 0,
        "remainingChallenges": 0,
    }


def test_no_completed_attempts(catalogue):
    result = compute_challenge_completion("u1", {"challenge_attempts": []})
    assert result["allChallengesCompleted"] is False
    assert result["completedChallenges"] == 0
    assert result["totalChallenges"] == 3
    assert result["remainingChallenges"] == 3


def test_partial_completion(catalogue):
    store = {
        "challenge_attempts": [
            _attempt("u1", "busDriver-001"),
            _attempt("u1", "library-001"),
        ]
    }
    result = compute_challenge_completion("u1", store)
    assert result["allChallengesCompleted"] is False
    assert result["completedChallenges"] == 2
    assert result["remainingChallenges"] == 1


def test_all_challenges_completed(catalogue):
    store = {
        "challenge_attempts": [
            _attempt("u1", "busDriver-001"),
            _attempt("u1", "library-001"),
            _attempt("u1", "classroom-001", completed=True, at="2026-01-02T00:00:00"),
        ]
    }
    result = compute_challenge_completion("u1", store)
    assert result["allChallengesCompleted"] is True
    assert result["completedChallenges"] == 3
    assert result["totalChallenges"] == 3
    assert result["remainingChallenges"] == 0


def test_duplicate_attempts_count_once(catalogue):
    store = {
        "challenge_attempts": [
            _attempt("u1", "busDriver-001", at="2026-01-01T00:00:00"),
            _attempt("u1", "busDriver-001", at="2026-01-02T00:00:00"),
            _attempt("u1", "library-001"),
            _attempt("u1", "classroom-001"),
        ]
    }
    result = compute_challenge_completion("u1", store)
    assert result["completedChallenges"] == 3
    assert result["allChallengesCompleted"] is True


def test_incomplete_attempts_do_not_count(catalogue):
    store = {
        "challenge_attempts": [
            _attempt("u1", "busDriver-001", completed=False),
            _attempt("u1", "library-001"),
            _attempt("u1", "classroom-001"),
        ]
    }
    result = compute_challenge_completion("u1", store)
    assert result["completedChallenges"] == 2
    assert result["allChallengesCompleted"] is False


def test_other_user_attempts_do_not_count(catalogue):
    store = {
        "challenge_attempts": [
            _attempt("other", "busDriver-001"),
            _attempt("other", "library-001"),
            _attempt("other", "classroom-001"),
            _attempt("u1", "busDriver-001"),
        ]
    }
    result = compute_challenge_completion("u1", store)
    assert result["completedChallenges"] == 1
    assert result["allChallengesCompleted"] is False


def test_unknown_legacy_ids_do_not_count(catalogue):
    store = {
        "challenge_attempts": [
            _attempt("u1", "legacy-gone"),
            _attempt("u1", "busDriver-001"),
            _attempt("u1", "library-001"),
            _attempt("u1", "classroom-001"),
        ]
    }
    result = compute_challenge_completion("u1", store)
    assert result["completedChallenges"] == 3
    assert result["allChallengesCompleted"] is True


def test_new_catalogue_challenge_reopens_completion(catalogue, monkeypatch):
    store = {
        "challenge_attempts": [
            _attempt("u1", "busDriver-001"),
            _attempt("u1", "library-001"),
            _attempt("u1", "classroom-001"),
        ]
    }
    assert compute_challenge_completion("u1", store)["allChallengesCompleted"] is True

    expanded = catalogue + [_challenge("new-001")]
    monkeypatch.setattr("app.repositories.get_challenges", lambda: expanded)
    result = compute_challenge_completion("u1", store)
    assert result["allChallengesCompleted"] is False
    assert result["remainingChallenges"] == 1
    assert result["totalChallenges"] == 4


def test_practice_returns_none_when_all_completed(catalogue):
    store = {
        "challenge_attempts": [
            _attempt("u1", "busDriver-001"),
            _attempt("u1", "library-001"),
            _attempt("u1", "classroom-001"),
        ]
    }
    assert get_next_practice_challenge("u1", store) is None


def test_practice_still_available_when_remaining(catalogue):
    store = {
        "skill_scores": [],
        "challenge_attempts": [
            _attempt("u1", "busDriver-001"),
        ]
    }
    next_challenge = get_next_practice_challenge("u1", store)
    assert next_challenge is not None
    assert next_challenge["id"] in {"library-001", "classroom-001"}


@pytest.fixture()
def client(tmp_path, monkeypatch, catalogue):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    store = {
        "users": [
            {
                "id": "user-1",
                "username": "tester",
                "email": None,
                "createdAt": "2026-01-01T00:00:00",
                "lastActiveAt": "2026-01-01T00:00:00",
            }
        ],
        "profiles": [
            {
                "id": "profile-1",
                "userId": "user-1",
                "avatarId": "avatar-detective-1",
                "displayName": "tester",
                "currentLevel": 1,
                "totalXp": 100,
                "currentLevelXp": 100,
                "dailyStreak": 0,
                "onboardingCompleted": True,
                "colorBlindness": False,
                "ageBand": "11_13",
                "lastChallengeId": None,
                "lastChallengeProgress": None,
                "settings": {"notifications": True, "sound": True, "privacy": False},
            }
        ],
        "skill_scores": [],
        "challenge_attempts": [],
        "xp_transactions": [],
        "detective_tips": [],
        "daily_missions": [],
        "daily_challenge_cache": {"date": None, "challengeId": None},
        "user_badges": [],
        "notifications": [],
    }
    (data_dir / "store.json").write_text(json.dumps(store))
    monkeypatch.setenv("DATA_DIR", str(data_dir))

    from app.config import settings

    monkeypatch.setattr(settings, "data_dir", str(data_dir))
    monkeypatch.setattr(settings, "hint_engine_enabled", False)

    import app.repositories as repo

    repo._challenges_cache = None
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client, store, data_dir

    repo._challenges_cache = None


def _write_store(data_dir, store):
    (data_dir / "store.json").write_text(json.dumps(store))


def test_home_includes_challenge_completion(client):
    test_client, _store, _data_dir = client
    home = test_client.get("/api/v1/home/user-1").json()
    assert "challengeCompletion" in home
    assert "greeting" in home
    assert "progress" in home
    assert home["challengeCompletion"]["allChallengesCompleted"] is False
    assert home["challengeCompletion"]["totalChallenges"] == 3


def test_practice_and_daily_api_return_completed_state(client, catalogue):
    test_client, store, data_dir = client
    store["challenge_attempts"] = [
        _attempt("user-1", "busDriver-001"),
        _attempt("user-1", "library-001"),
        _attempt("user-1", "classroom-001"),
    ]
    _write_store(data_dir, store)

    practice = test_client.get("/api/v1/challenges/users/user-1/next-practice")
    assert practice.status_code == 200
    body = practice.json()
    assert body["status"] == ALL_CHALLENGES_COMPLETED_STATUS
    assert body["challenge"] is None
    assert body["nextRoute"] == ALL_CHALLENGES_COMPLETED_NEXT_ROUTE

    daily = test_client.get("/api/v1/challenges/users/user-1/daily")
    assert daily.status_code == 200
    daily_body = daily.json()
    assert daily_body["status"] == ALL_CHALLENGES_COMPLETED_STATUS
    assert daily_body["challenge"] is None
    assert daily_body["completed"] is True

    home = test_client.get("/api/v1/home/user-1").json()
    assert home["challengeCompletion"]["allChallengesCompleted"] is True
    assert home["dailyMission"]["challengeId"] is None


def test_daily_still_available_when_remaining(client):
    test_client, store, data_dir = client
    store["challenge_attempts"] = [_attempt("user-1", "busDriver-001")]
    _write_store(data_dir, store)

    daily = test_client.get("/api/v1/challenges/users/user-1/daily")
    assert daily.status_code == 200
    body = daily.json()
    assert body.get("status") != ALL_CHALLENGES_COMPLETED_STATUS
    assert body["challenge"] is not None
    assert body["challenge"]["id"] in {
        "busDriver-001",
        "library-001",
        "classroom-001",
    }
