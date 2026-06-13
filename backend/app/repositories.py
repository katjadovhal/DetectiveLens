import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from app.constants import DEMO_USER_ID, LEVELS, SKILL_CATEGORIES, XP_RULES
from app.services.challenge_helpers import strip_correct_answer
from app.services.demo_user import ensure_demo_user
from app.services.personalization import get_detective_tip
from app.storage import (
    find_by_id_or_slug,
    find_one,
    load_store,
    new_id,
    now_iso,
    save_store,
    with_store,
)

CHALLENGE_DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "challenge-data"

_challenges_cache: list[dict] | None = None


def _load_challenges_from_files() -> list[dict]:
    global _challenges_cache
    if _challenges_cache is not None:
        return _challenges_cache

    challenges = []
    for path in CHALLENGE_DATA_ROOT.rglob("*.json"):
        if path.name == "README.md":
            continue
        data = json.loads(path.read_text())
        challenge_id = data.get("id") or data["slug"]
        hints = [
            {
                "id": h["id"],
                "challengeId": challenge_id,
                "order": h["order"],
                "question": h["question"],
                "content": h["content"],
                "skillCategoryId": h["skillCategoryId"],
            }
            for h in data.get("hints", [])
        ]
        challenges.append(
            {
                "id": challenge_id,
                "slug": data["slug"],
                "type": data["type"],
                "difficulty": data["difficulty"],
                "title": data["title"],
                "instruction": data["instruction"],
                "content": data["content"],
                "skillCategoryIds": data["skillCategoryIds"],
                "xpReward": data["xpReward"],
                "isDailyEligible": data.get("isDailyEligible", True),
                "active": data.get("active", True),
                "hints": hints,
            }
        )

    _challenges_cache = challenges
    return challenges


def get_challenges() -> list[dict]:
    return [c for c in _load_challenges_from_files() if c.get("active", True)]


def get_challenge(challenge_id: str) -> dict | None:
    return find_by_id_or_slug(get_challenges(), challenge_id)


def serialize_challenge(challenge: dict, include_hints: bool = False) -> dict:
    data = {
        "id": challenge["id"],
        "slug": challenge["slug"],
        "type": challenge["type"],
        "difficulty": challenge["difficulty"],
        "title": challenge["title"],
        "instruction": challenge["instruction"],
        "content": strip_correct_answer(challenge["type"], challenge["content"]),
        "skillCategoryIds": challenge["skillCategoryIds"],
        "xpReward": challenge["xpReward"],
        "isDailyEligible": challenge["isDailyEligible"],
    }
    if include_hints:
        data["hints"] = challenge.get("hints", [])
    return data


def get_demo_user(store: dict | None = None) -> dict | None:
    s = store if store is not None else load_store()
    return find_one(s["users"], id=DEMO_USER_ID) or find_one(s["users"], username="demo")


def get_demo_profile(store: dict | None = None) -> dict | None:
    s = store if store is not None else load_store()
    user = get_demo_user(s)
    if not user:
        return None
    return find_one(s["profiles"], userId=user["id"])


def get_home_data() -> dict:
    profile = get_demo_profile()
    current_level = profile["currentLevel"] if profile else 4
    total_xp = profile["totalXp"] if profile else 320

    level_info = next((l for l in LEVELS if l["level"] == current_level), LEVELS[3])
    next_level = next((l for l in LEVELS if l["level"] == current_level + 1), None)
    xp_to_next = max(0, (next_level["xp_required"] - total_xp) if next_level else 880)

    daily_challenge = get_challenge("burger-king-001")

    return {
        "greeting": {
            "displayName": profile["displayName"] if profile else "Alex",
            "levelTitle": level_info["title"],
            "avatarId": profile["avatarId"] if profile else "detective-default",
        },
        "progress": {
            "totalXp": total_xp,
            "currentLevelXp": profile["currentLevelXp"] if profile else 320,
            "xpToNextLevel": xp_to_next,
            "level": current_level,
        },
        "dailyMission": {
            "challengeId": daily_challenge["id"] if daily_challenge else "burger-king-001",
            "title": "Daily Mission!",
            "description": "Spot the fake post",
            "xpBonus": 100,
            "completed": False,
        },
        "continueLearning": {
            "challengeId": (profile["lastChallengeId"] if profile else None)
            or (daily_challenge["id"] if daily_challenge else None),
            "title": daily_challenge["title"] if daily_challenge else "Which post is fake?",
        },
        "recommendedChallenges": [
            {
                "id": daily_challenge["id"] if daily_challenge else "burger-king-001",
                "title": "Which post is fake?",
                "type": "fake_post",
                "reason": "Practice source verification",
            }
        ],
    }


def get_profile_data() -> dict:
    profile = get_demo_profile()
    if not profile:
        return {
            "profile": {
                "displayName": "Alex",
                "avatarId": "detective-default",
                "selfReportedLevel": "beginner",
                "currentLevel": 4,
                "totalXp": 320,
                "onboardingCompleted": False,
            }
        }

    return {
        "profile": {
            "id": profile["id"],
            "userId": profile["userId"],
            "avatarId": profile["avatarId"],
            "displayName": profile["displayName"],
            "selfReportedLevel": profile["selfReportedLevel"],
            "currentLevel": profile["currentLevel"],
            "totalXp": profile["totalXp"],
            "currentLevelXp": profile["currentLevelXp"],
            "dailyStreak": profile["dailyStreak"],
            "onboardingCompleted": profile["onboardingCompleted"],
            "settings": profile["settings"],
        }
    }


@with_store
def update_profile(store: dict, body: dict) -> dict:
    profile = get_demo_profile(store)
    if not profile:
        raise ValueError("Profile not found")

    if body.get("displayName") is not None:
        profile["displayName"] = body["displayName"]
    if body.get("avatarId") is not None:
        profile["avatarId"] = body["avatarId"]
    if body.get("selfReportedLevel") is not None:
        profile["selfReportedLevel"] = body["selfReportedLevel"]
    if body.get("settings") is not None:
        profile["settings"] = {**profile["settings"], **body["settings"]}

    return {
        "profile": {
            "id": profile["id"],
            "displayName": profile["displayName"],
            "avatarId": profile["avatarId"],
            "selfReportedLevel": profile["selfReportedLevel"],
            "settings": profile["settings"],
        }
    }


@with_store
def complete_onboarding(store: dict, level: str) -> dict:
    user = get_demo_user(store)
    if not user:
        user = {
            "id": DEMO_USER_ID,
            "username": "demo",
            "email": "demo@detectivelens.local",
            "createdAt": now_iso(),
            "lastActiveAt": now_iso(),
        }
        store["users"].append(user)

    profile = get_demo_profile(store)
    if profile:
        profile["selfReportedLevel"] = level
        profile["onboardingCompleted"] = True
    else:
        store["profiles"].append(
            {
                "id": new_id(),
                "userId": DEMO_USER_ID,
                "avatarId": "detective-default",
                "displayName": "Alex",
                "selfReportedLevel": level,
                "currentLevel": 1,
                "totalXp": 0,
                "currentLevelXp": 0,
                "dailyStreak": 0,
                "onboardingCompleted": True,
                "lastChallengeId": None,
                "lastChallengeProgress": None,
                "settings": {"notifications": True, "sound": True, "privacy": False},
            }
        )

    return {"success": True, "redirectTo": "/"}


@with_store
def start_challenge(store: dict, challenge_id: str) -> dict:
    challenge = get_challenge(challenge_id)
    if not challenge:
        raise ValueError("Challenge not found")

    ensure_demo_user(store)
    attempt = {
        "id": new_id(),
        "userId": DEMO_USER_ID,
        "challengeId": challenge["id"],
        "startedAt": now_iso(),
        "completedAt": None,
        "selectedAnswer": None,
        "isCorrect": None,
        "hintsUsed": 0,
        "hintsViewed": [],
        "timeSpentMs": None,
        "xpEarned": 0,
        "scoreBreakdown": None,
    }
    store["challenge_attempts"].append(attempt)
    return {"sessionId": attempt["id"], "challengeId": challenge["id"]}


@with_store
def submit_challenge(store: dict, session_id: str, body: dict) -> dict:
    attempt = find_one(store["challenge_attempts"], id=session_id)
    if not attempt:
        raise ValueError("Session not found")

    challenge = get_challenge(attempt["challengeId"])
    if not challenge:
        raise ValueError("Challenge not found")

    content = challenge["content"]
    correct_post_id = content.get("correctPostId")
    is_correct = body["selectedPostId"] == correct_post_id
    hint_penalty = body.get("hintsUsed", 0) * XP_RULES["HINT_PENALTY"]
    xp_earned = max(0, challenge["xpReward"] - hint_penalty) if is_correct else 0

    attempt["selectedAnswer"] = body["selectedPostId"]
    attempt["isCorrect"] = is_correct
    attempt["hintsUsed"] = body.get("hintsUsed", 0)
    attempt["timeSpentMs"] = body.get("timeSpentMs")
    attempt["xpEarned"] = xp_earned
    attempt["completedAt"] = now_iso()

    profile = get_demo_profile(store)
    if xp_earned > 0 and profile:
        profile["totalXp"] += xp_earned
        profile["currentLevelXp"] += xp_earned
        profile["lastChallengeId"] = attempt["challengeId"]
        store["xp_transactions"].append(
            {
                "id": new_id(),
                "userId": attempt["userId"],
                "amount": xp_earned,
                "source": "challenge",
                "referenceId": attempt["id"],
                "createdAt": now_iso(),
            }
        )

    tip = get_detective_tip(
        is_correct=is_correct,
        selected_answer=body["selectedPostId"],
        correct_answer=correct_post_id,
        challenge_type=challenge["type"],
    )

    explanation = content.get("explanation", {}).get("bullets", [])
    updated_xp = profile["totalXp"] if profile else None

    return {
        "attemptId": attempt["id"],
        "isCorrect": is_correct,
        "selectedAnswer": body["selectedPostId"],
        "correctAnswer": correct_post_id,
        "explanation": explanation,
        "xpEarned": xp_earned,
        "detectiveTip": tip.to_dict() if tip else None,
        "updatedXp": updated_xp,
    }


def get_skill_profile() -> dict:
    store = load_store()
    scores = [s for s in store["skill_scores"] if s.get("userId") == DEMO_USER_ID]

    if not scores:
        return {
            "skillProfile": [
                {"categoryId": "source_verification", "score": 45, "attempts": 0, "correct": 0},
                {"categoryId": "content_authenticity", "score": 50, "attempts": 0, "correct": 0},
            ]
        }

    categories = {c["id"]: c for c in SKILL_CATEGORIES}
    return {
        "skillProfile": [
            {
                "categoryId": s["categoryId"],
                "score": s["score"],
                "attempts": s["attempts"],
                "correct": s["correct"],
                "categoryName": categories.get(s["categoryId"], {}).get("name"),
            }
            for s in scores
        ]
    }


def get_weak_areas_data() -> dict:
    from app.services.personalization import get_weak_areas

    store = load_store()
    scores = [s for s in store["skill_scores"] if s.get("userId") == DEMO_USER_ID]
    mapped = [
        {
            "categoryId": s["categoryId"],
            "score": s["score"],
            "attempts": s["attempts"],
            "correct": s["correct"],
        }
        for s in scores
    ]
    weak = get_weak_areas(mapped) if mapped else [
        {"categoryId": "source_verification", "score": 45, "attempts": 0, "correct": 0}
    ]
    return {"weakAreas": weak}


def get_recommendations() -> dict:
    challenge = get_challenge("burger-king-001")
    return {
        "recommendations": [
            {
                "id": challenge["id"] if challenge else "burger-king-001",
                "title": "Which post is fake?",
                "type": "fake_post",
                "reason": "Targets your weak area: Source Verification",
            }
        ]
    }
