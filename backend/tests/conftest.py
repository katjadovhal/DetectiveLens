import json

import pytest

from app.config import settings


@pytest.fixture()
def temp_store(tmp_path, monkeypatch):
    store_dir = tmp_path / "data"
    store_dir.mkdir()
    store_path = store_dir / "store.json"
    store_path.write_text(
        json.dumps(
            {
                "users": [{"id": "user-1", "username": "tester"}],
                "profiles": [
                    {
                        "id": "profile-1",
                        "userId": "user-1",
                        "avatarId": "avatar-detective-1",
                        "displayName": "Tester",
                        "currentLevel": 1,
                        "totalXp": 500,
                        "currentLevelXp": 500,
                        "dailyStreak": 0,
                        "onboardingCompleted": True,
                        "ageBand": "11_13",
                        "youngReader": False,
                        "settings": {
                            "notifications": True,
                            "sound": True,
                            "privacy": False,
                        },
                        "hqOwnedItemIds": ["desk-dark"],
                    }
                ],
                "skill_scores": [],
                "challenge_attempts": [],
                "xp_transactions": [],
                "detective_tips": [],
                "daily_missions": [],
                "daily_challenge_cache": {"date": None, "challengeId": None},
            }
        )
    )
    monkeypatch.setattr(settings, "data_dir", str(store_dir))
    # Tests use deterministic fallbacks; Ollama is not required.
    monkeypatch.setattr(settings, "hint_engine_enabled", False)
    return store_path
