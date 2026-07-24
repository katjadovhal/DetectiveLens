import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
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
                "totalXp": 0,
                "currentLevelXp": 0,
                "dailyStreak": 0,
                "onboardingCompleted": True,
                "colorBlindness": False,
                "ageBand": "11_13",
                "lastChallengeId": None,
                "lastChallengeProgress": None,
                "settings": {"notifications": True, "sound": True, "privacy": False},
            }
        ],
        "skill_scores": [
            {
                "id": "s1",
                "userId": "user-1",
                "categoryId": "backgrounds",
                "score": 0,
                "attempts": 0,
                "correct": 0,
            },
            {
                "id": "s2",
                "userId": "user-1",
                "categoryId": "content_authenticity",
                "score": 0,
                "attempts": 0,
                "correct": 0,
            },
        ],
        "challenge_attempts": [],
        "xp_transactions": [],
        "detective_tips": [],
        "daily_missions": [],
        "daily_challenge_cache": {"date": None, "challengeId": None},
    }
    (data_dir / "store.json").write_text(json.dumps(store))

    monkeypatch.setenv("DATA_DIR", str(data_dir))

    from app.config import settings

    monkeypatch.setattr(settings, "data_dir", str(data_dir))

    import app.repositories as repo

    repo._challenges_cache = None

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

    repo._challenges_cache = None


def test_pre_answer_hint_ok(client):
    res = client.post(
        "/api/v1/challenges/class-001/hint",
        json={"userId": "user-1", "stage": "pre_answer_hint", "locale": "en"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["stage"] == "pre_answer_hint"
    assert body["personalizationMode"] == "neutral"
    assert body["locale"] == "en"
    assert body["ageBand"] == "11_13"
    assert body["text"]
    assert "Image B was generated" not in body["text"]


def test_answer_explanation_forbidden_without_attempt(client):
    res = client.post(
        "/api/v1/challenges/class-001/hint",
        json={"userId": "user-1", "stage": "answer_explanation"},
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "HINT_STAGE_FORBIDDEN"


def test_answer_explanation_after_submit(client):
    start = client.post("/api/v1/challenges/class-001/start/user-1")
    assert start.status_code == 200
    session_id = start.json()["sessionId"]

    submit = client.post(
        f"/api/v1/challenges/sessions/{session_id}/submit",
        json={"selectedPostId": "A", "hintsUsed": 0},
    )
    assert submit.status_code == 200

    res = client.post(
        "/api/v1/challenges/class-001/hint",
        json={
            "userId": "user-1",
            "stage": "answer_explanation",
            "attemptNumber": 1,
            "selectedOption": "A",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["stage"] == "answer_explanation"
    assert body["source"] in {"grounding", "explanation"}
    assert "AI" in body["text"] or "photograph" in body["text"]


def test_tampered_selected_option_forbidden(client):
    start = client.post("/api/v1/challenges/class-001/start/user-1")
    session_id = start.json()["sessionId"]
    client.post(
        f"/api/v1/challenges/sessions/{session_id}/submit",
        json={"selectedPostId": "A"},
    )

    res = client.post(
        "/api/v1/challenges/class-001/hint",
        json={
            "userId": "user-1",
            "stage": "answer_explanation",
            "selectedOption": "B",
        },
    )
    assert res.status_code == 403


def test_unknown_challenge_and_user(client):
    missing_challenge = client.post(
        "/api/v1/challenges/does-not-exist/hint",
        json={"userId": "user-1", "stage": "pre_answer_hint"},
    )
    assert missing_challenge.status_code == 404

    missing_user = client.post(
        "/api/v1/challenges/class-001/hint",
        json={"userId": "missing-user", "stage": "pre_answer_hint"},
    )
    assert missing_user.status_code == 404


def test_create_user_persists_age_band(client):
    res = client.post(
        "/api/v1/onboarding/create-user",
        json={
            "username": "kiddo",
            "age": 9,
            "colorBlindness": False,
            "avatarId": "avatar-detective-2",
        },
    )
    assert res.status_code == 200
    user_id = res.json()["userId"]

    profile = client.get(f"/api/v1/profiles/{user_id}")
    assert profile.status_code == 200
    assert profile.json()["profile"]["ageBand"] == "8_10"
    assert "age" not in profile.json()["profile"]


def test_health_and_hint_without_ollama(client, monkeypatch):
    monkeypatch.setattr("app.services.hint_engine.settings.hint_engine_enabled", False)
    health = client.get("/api/v1/health")
    assert health.status_code == 200

    hint = client.post(
        "/api/v1/challenges/monkey-001/hint",
        json={"userId": "user-1", "stage": "pre_answer_hint", "locale": "de"},
    )
    assert hint.status_code == 200
    assert hint.json()["locale"] == "en"
    assert hint.json()["source"] != "model"


def test_pilot_skills_are_canonical(client):
    res = client.get("/api/v1/challenges")
    assert res.status_code == 200
    from app.constants import CANONICAL_SKILL_IDS

    for challenge in res.json()["challenges"]:
        for skill_id in challenge["skillCategoryIds"]:
            assert skill_id in CANONICAL_SKILL_IDS
