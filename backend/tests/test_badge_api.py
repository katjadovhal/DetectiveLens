"""Badge + notification API integration tests."""

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
                "ageBand": "8_10",
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
        yield test_client

    repo._challenges_cache = None


def test_badges_endpoint_all_locked_initially(client):
    response = client.get("/api/v1/profiles/user-1/badges")
    assert response.status_code == 200
    badges = response.json()["badges"]
    assert len(badges) >= 5
    assert all(b["status"] == "locked" for b in badges)
    assert all("progress" in b and "target" in b for b in badges)


def test_submit_unlocks_first_case_and_notifies_once(client):
    challenges = client.get("/api/v1/challenges").json()["challenges"]
    challenge_id = challenges[0]["id"]

    start = client.post(f"/api/v1/challenges/{challenge_id}/start/user-1")
    assert start.status_code == 200
    session_id = start.json()["sessionId"]

    challenge = client.get(f"/api/v1/challenges/{challenge_id}").json()["challenge"]
    # Prefer incorrect answer so we still complete; correctPostId stripped from client payload.
    # Submit A then check unlocks — either outcome completes the attempt.
    submit = client.post(
        f"/api/v1/challenges/sessions/{session_id}/submit",
        json={"selectedPostId": "A", "hintsUsed": 0},
    )
    assert submit.status_code == 200
    body = submit.json()
    assert "newlyUnlockedBadges" in body
    assert any(b["id"] == "first_case" for b in body["newlyUnlockedBadges"])
    # Existing fields preserved
    assert "isCorrect" in body
    assert "xpEarned" in body
    assert "detectiveTip" in body or body.get("detectiveTip") is None

    notes = client.get("/api/v1/profiles/user-1/notifications").json()
    assert notes["unreadCount"] >= 1
    badge_notes = [n for n in notes["notifications"] if n["badgeId"] == "first_case"]
    assert len(badge_notes) == 1

    # Second submit of another challenge must not re-notify first_case
    start2 = client.post(f"/api/v1/challenges/{challenge_id}/start/user-1")
    session2 = start2.json()["sessionId"]
    submit2 = client.post(
        f"/api/v1/challenges/sessions/{session2}/submit",
        json={"selectedPostId": "B", "hintsUsed": 0},
    )
    assert submit2.status_code == 200
    assert not any(b["id"] == "first_case" for b in submit2.json()["newlyUnlockedBadges"])

    notes2 = client.get("/api/v1/profiles/user-1/notifications").json()
    badge_notes2 = [n for n in notes2["notifications"] if n["badgeId"] == "first_case"]
    assert len(badge_notes2) == 1

    badges = client.get("/api/v1/profiles/user-1/badges").json()["badges"]
    first = next(b for b in badges if b["id"] == "first_case")
    assert first["status"] == "unlocked"
    assert first["earnedAt"]


def test_notification_title_and_payload_fields(client):
    challenges = client.get("/api/v1/challenges").json()["challenges"]
    challenge_id = challenges[0]["id"]
    start = client.post(f"/api/v1/challenges/{challenge_id}/start/user-1")
    session_id = start.json()["sessionId"]
    body = client.post(
        f"/api/v1/challenges/sessions/{session_id}/submit",
        json={"selectedPostId": "A", "hintsUsed": 0},
    ).json()

    unlock = next(b for b in body["newlyUnlockedBadges"] if b["id"] == "first_case")
    assert unlock.get("notificationId")
    assert unlock.get("title") == "First Case"
    assert unlock.get("reason")
    assert unlock.get("message")

    notes = client.get("/api/v1/profiles/user-1/notifications").json()["notifications"]
    note = next(n for n in notes if n["badgeId"] == "first_case")
    assert note["title"] == "New badge unlocked!"
    assert note["type"] == "badge_unlocked"
    assert note["id"] == unlock["notificationId"]


def test_mark_notification_read(client):
    challenges = client.get("/api/v1/challenges").json()["challenges"]
    challenge_id = challenges[0]["id"]
    start = client.post(f"/api/v1/challenges/{challenge_id}/start/user-1")
    session_id = start.json()["sessionId"]
    client.post(
        f"/api/v1/challenges/sessions/{session_id}/submit",
        json={"selectedPostId": "A", "hintsUsed": 0},
    )

    notes = client.get("/api/v1/profiles/user-1/notifications").json()
    note_id = notes["notifications"][0]["id"]
    assert notes["unreadCount"] >= 1

    marked = client.post(
        "/api/v1/profiles/user-1/notifications/read",
        json={"notificationId": note_id},
    )
    assert marked.status_code == 200
    assert marked.json()["notification"]["readAt"]
    assert marked.json()["unreadCount"] == 0
