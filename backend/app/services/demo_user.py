from app.constants import DEMO_USER_ID
from app.storage import find_one, load_store, new_id, now_iso, save_store


def ensure_demo_user(store: dict | None = None) -> dict:
    if store is None:
        store = load_store()
        user = find_one(store["users"], id=DEMO_USER_ID) or find_one(store["users"], username="demo")
        if user:
            return user

        user = {
            "id": DEMO_USER_ID,
            "username": "demo",
            "email": "demo@detectivelens.local",
            "createdAt": now_iso(),
            "lastActiveAt": now_iso(),
        }
        profile = {
            "id": new_id(),
            "userId": DEMO_USER_ID,
            "avatarId": "detective-default",
            "displayName": "Alex",
            "selfReportedLevel": "beginner",
            "currentLevel": 4,
            "totalXp": 320,
            "currentLevelXp": 320,
            "dailyStreak": 0,
            "onboardingCompleted": True,
            "lastChallengeId": None,
            "lastChallengeProgress": None,
            "settings": {"notifications": True, "sound": True, "privacy": False},
        }
        store["users"].append(user)
        store["profiles"].append(profile)
        save_store(store)
        return user

    user = find_one(store["users"], id=DEMO_USER_ID) or find_one(store["users"], username="demo")
    if user:
        return user

    user = {
        "id": DEMO_USER_ID,
        "username": "demo",
        "email": "demo@detectivelens.local",
        "createdAt": now_iso(),
        "lastActiveAt": now_iso(),
    }
    profile = {
        "id": new_id(),
        "userId": DEMO_USER_ID,
        "avatarId": "detective-default",
        "displayName": "Alex",
        "selfReportedLevel": "beginner",
        "currentLevel": 4,
        "totalXp": 320,
        "currentLevelXp": 320,
        "dailyStreak": 0,
        "onboardingCompleted": True,
        "lastChallengeId": None,
        "lastChallengeProgress": None,
        "settings": {"notifications": True, "sound": True, "privacy": False},
    }
    store["users"].append(user)
    store["profiles"].append(profile)
    return user
