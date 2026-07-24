import json
import random
from copy import deepcopy
from datetime import datetime, date
from pathlib import Path

from app.constants import (
    DEFAULT_AGE_BAND,
    DIFFICULTY_MAP,
    LEVELS,
    SKILL_CATEGORIES,
    WEIGHT_WEAKNESS,
    WEIGHT_DIFFICULTY_FIT,
    XP_RULES,
    age_to_age_band,
    canonicalize_skill_id,
    canonicalize_skill_ids,
    normalize_avatar_id,
)
from app.services.challenge_helpers import strip_correct_answer
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
                "skillCategoryIds": canonicalize_skill_ids(data.get("skillCategoryIds")),
                "xpReward": data["xpReward"],
                "isDailyEligible": data.get("isDailyEligible", True),
                "active": data.get("active", True),
                "hints": hints,
                "grounding": data.get("grounding"),
                "hintFallbacks": data.get("hintFallbacks"),
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


def get_user(user_id: str, store: dict | None = None) -> dict | None:
    s = store if store is not None else load_store()
    return find_one(s["users"], id=user_id)


def get_profile(user_id: str, store: dict | None = None) -> dict | None:
    s = store if store is not None else load_store()
    return find_one(s["profiles"], userId=user_id)


def get_all_users(store: dict | None = None) -> list[dict]:
    s = store if store is not None else load_store()
    return s.get("users", [])


def get_level_info(level: int) -> dict:
    return next((l for l in LEVELS if l["level"] == level), LEVELS[0])


def apply_level_up(profile: dict) -> bool:
    leveled_up = False
    while True:
        xp_needed = get_level_info(profile["currentLevel"]).get("xp_to_advance")
        if xp_needed is None or profile["currentLevelXp"] < xp_needed:
            break
        profile["currentLevelXp"] = 0
        profile["currentLevel"] += 1
        leveled_up = True
    return leveled_up


def get_home_data(user_id: str, store: dict | None = None) -> dict:
    s = store if store is not None else load_store()
    profile = get_profile(user_id, s)
    current_level = profile["currentLevel"] if profile else 1
    total_xp = profile["totalXp"] if profile else 0
    current_level_xp = profile["currentLevelXp"] if profile else 0

    level_info = get_level_info(current_level)
    level_xp_required = level_info.get("xp_to_advance")
    if level_xp_required is not None:
        xp_to_next = max(0, level_xp_required - current_level_xp)
    else:
        level_xp_required = max(current_level_xp, 1)
        xp_to_next = 0

    daily_challenge = get_daily_challenge(s)

    return {
        "greeting": {
            "displayName": profile["displayName"] if profile else "Detektiv",
            "levelTitle": level_info["title"],
            "avatarId": normalize_avatar_id(profile["avatarId"] if profile else None),
        },
        "progress": {
            "totalXp": total_xp,
            "currentLevelXp": current_level_xp,
            "xpToNextLevel": xp_to_next,
            "levelXpRequired": level_xp_required,
            "level": current_level,
        },
        "dailyMission": {
            "challengeId": daily_challenge["id"] if daily_challenge else None,
            "title": "Daily Mission!",
            "description": daily_challenge["title"] if daily_challenge else "Spot the fake post",
            "xpBonus": 100,
            "completed": False,
        },
    }


def _completed_challenge_count(user_id: str, store: dict) -> int:
    completed_ids = {
        attempt["challengeId"]
        for attempt in store.get("challenge_attempts", [])
        if attempt.get("userId") == user_id
        and attempt.get("completedAt")
        and attempt.get("isCorrect") is True
    }
    return len(completed_ids)


def get_profile_data(user_id: str, store: dict | None = None) -> dict:
    s = store if store is not None else load_store()
    profile = get_profile(user_id, s)
    if not profile:
        return {
            "profile": {
                "displayName": "Detektiv",
                "avatarId": normalize_avatar_id(None),
                "currentLevel": 1,
                "totalXp": 0,
                "currentLevelXp": 0,
                "completedChallengeCount": 0,
                "onboardingCompleted": False,
                "colorBlindness": False,
                "ageBand": DEFAULT_AGE_BAND,
            }
        }

    return {
        "profile": {
            "id": profile["id"],
            "userId": profile["userId"],
            "avatarId": normalize_avatar_id(profile.get("avatarId")),
            "displayName": profile["displayName"],
            "currentLevel": profile["currentLevel"],
            "totalXp": profile["totalXp"],
            "currentLevelXp": profile["currentLevelXp"],
            "dailyStreak": profile["dailyStreak"],
            "completedChallengeCount": _completed_challenge_count(user_id, s),
            "onboardingCompleted": profile["onboardingCompleted"],
            "colorBlindness": profile.get("colorBlindness", False),
            "ageBand": profile.get("ageBand", DEFAULT_AGE_BAND),
            "settings": profile["settings"],
        }
    }


@with_store
def update_profile(store: dict, user_id: str, body: dict) -> dict:
    profile = get_profile(user_id, store)
    if not profile:
        raise ValueError("Profile not found")

    if body.get("displayName") is not None:
        profile["displayName"] = body["displayName"]
    if body.get("avatarId") is not None:
        # Coerce legacy/unknown IDs; do not mutate unrelated fields.
        profile["avatarId"] = normalize_avatar_id(body["avatarId"])
    if body.get("settings") is not None:
        profile["settings"] = {**profile["settings"], **body["settings"]}

    return {
        "profile": {
            "id": profile["id"],
            "displayName": profile["displayName"],
            "avatarId": normalize_avatar_id(profile.get("avatarId")),
            "settings": profile["settings"],
        }
    }


@with_store
def create_user(store: dict, body: dict) -> dict:
    """Create a new user during onboarding"""
    # Check if username already exists
    existing = find_one(store["users"], username=body["username"])
    if existing:
        raise ValueError("Username already exists")

    user_id = new_id()
    user = {
        "id": user_id,
        "username": body["username"],
        "email": None,
        "createdAt": now_iso(),
        "lastActiveAt": now_iso(),
    }
    store["users"].append(user)

    profile = {
        "id": new_id(),
        "userId": user_id,
        "avatarId": normalize_avatar_id(body.get("avatarId")),
        "displayName": body["username"],
        "currentLevel": 1,
        "totalXp": 0,
        "currentLevelXp": 0,
        "dailyStreak": 0,
        "onboardingCompleted": True,
        "colorBlindness": body.get("colorBlindness", False),
        "ageBand": age_to_age_band(int(body["age"])),
        "lastChallengeId": None,
        "lastChallengeProgress": None,
        "settings": {"notifications": True, "sound": True, "privacy": False},
    }
    store["profiles"].append(profile)

    # Initialize skill scores for the user
    for skill in SKILL_CATEGORIES:
        store["skill_scores"].append({
            "id": new_id(),
            "userId": user_id,
            "categoryId": skill["id"],
            "score": 0,
            "attempts": 0,
            "correct": 0,
        })

    return {
        "success": True,
        "userId": user_id,
        "redirectTo": f"/challenge-staging?userId={user_id}",
    }


@with_store
def start_challenge(store: dict, user_id: str, challenge_id: str) -> dict:
    challenge = get_challenge(challenge_id)
    if not challenge:
        raise ValueError("Challenge not found")

    prior_attempts = [
        a
        for a in store.get("challenge_attempts", [])
        if a.get("userId") == user_id and a.get("challengeId") == challenge["id"]
    ]
    attempt = {
        "id": new_id(),
        "userId": user_id,
        "challengeId": challenge["id"],
        "attemptNumber": len(prior_attempts) + 1,
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
    return {
        "sessionId": attempt["id"],
        "challengeId": challenge["id"],
        "attemptNumber": attempt["attemptNumber"],
    }


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

    profile = get_profile(attempt["userId"], store)
    if profile:
        profile["totalXp"] += xp_earned
        profile["currentLevelXp"] += xp_earned
        apply_level_up(profile)
        profile["lastChallengeId"] = attempt["challengeId"]

        # Update skill scores based on challenge result
        update_skill_profile(store, attempt["userId"], challenge, is_correct)

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
        "attemptNumber": attempt.get("attemptNumber"),
        "isCorrect": is_correct,
        "selectedAnswer": body["selectedPostId"],
        "correctAnswer": correct_post_id,
        "explanation": explanation,
        "xpEarned": xp_earned,
        "detectiveTip": tip.to_dict() if tip else None,
        "updatedXp": updated_xp,
    }


def get_skill_profile(user_id: str, store: dict | None = None) -> dict:
    s = store if store is not None else load_store()
    scores = [sc for sc in s["skill_scores"] if sc.get("userId") == user_id]

    if not scores:
        return {
            "skillProfile": [
                {"categoryId": "source_verification", "score": 0, "attempts": 0, "correct": 0},
                {"categoryId": "content_authenticity", "score": 0, "attempts": 0, "correct": 0},
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


def get_weak_areas_data(user_id: str, store: dict | None = None) -> dict:
    from app.services.personalization import get_weak_areas

    s = store if store is not None else load_store()
    scores = [sc for sc in s["skill_scores"] if sc.get("userId") == user_id]
    mapped = [
        {
            "categoryId": sc["categoryId"],
            "score": sc["score"],
            "attempts": sc["attempts"],
            "correct": sc["correct"],
        }
        for sc in scores
    ]
    weak = get_weak_areas(mapped) if mapped else [
        {"categoryId": "source_verification", "score": 0, "attempts": 0, "correct": 0}
    ]
    return {"weakAreas": weak}


def get_recommendations(user_id: str, store: dict | None = None) -> dict:
    s = store if store is not None else load_store()
    challenges = get_challenges()
    if not challenges:
        return {"recommendations": []}

    # Get a random challenge
    challenge = random.choice(challenges)
    return {
        "recommendations": [
            {
                "id": challenge["id"],
                "title": challenge["title"],
                "type": "fake_post",
                "reason": "Practice source verification",
            }
        ]
    }


def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp value between lo and hi"""
    return max(lo, min(x, hi))


def update_skill_profile(store: dict, user_id: str, challenge: dict, correct: bool) -> None:
    """Update user skill profile after a challenge using canonical skill ids only."""
    skill_categories = canonicalize_skill_ids(challenge.get("skillCategoryIds", []))
    if not skill_categories:
        return

    n = len(skill_categories)
    delta = (1 / n) if correct else -(1 / n)

    for skill_id in skill_categories:
        canonical = canonicalize_skill_id(skill_id)
        if not canonical:
            continue
        score_entry = find_one(store["skill_scores"], userId=user_id, categoryId=canonical)
        if score_entry:
            score_entry["score"] = clamp(score_entry["score"] + delta, -1, 1)
            score_entry["attempts"] = score_entry.get("attempts", 0) + 1
            if correct:
                score_entry["correct"] = score_entry.get("correct", 0) + 1


def weakness_signal(user_id: str, challenge: dict, store: dict) -> float:
    """Calculate weakness signal for challenge recommendation"""
    skill_categories = canonicalize_skill_ids(challenge.get("skillCategoryIds", []))
    if not skill_categories:
        return 0

    scores = []
    for skill_id in skill_categories:
        score_entry = find_one(store["skill_scores"], userId=user_id, categoryId=skill_id)
        skill_score = score_entry["score"] if score_entry else 0
        scores.append(-skill_score)  # negative to find weakest

    raw = max(scores) if scores else 0
    return clamp(raw, 0, 1)


def user_ability(user_id: str, challenge: dict, store: dict) -> float:
    """Get user ability for skills touched by this challenge"""
    skill_categories = canonicalize_skill_ids(challenge.get("skillCategoryIds", []))
    if not skill_categories:
        return 0

    relevant = []
    for skill_id in skill_categories:
        score_entry = find_one(store["skill_scores"], userId=user_id, categoryId=skill_id)
        skill_score = score_entry["score"] if score_entry else 0
        relevant.append(skill_score)

    return sum(relevant) / len(relevant) if relevant else 0


def difficulty_fit_signal(user_id: str, challenge: dict, store: dict) -> float:
    """Calculate difficulty fit signal"""
    challenge_level = DIFFICULTY_MAP.get(challenge.get("difficulty", "medium"), 0)
    ability = user_ability(user_id, challenge, store)
    ability_scaled = ability / 2

    distance = abs(challenge_level - ability_scaled)
    return 1 - clamp(distance, 0, 1)


def calculate_challenge_score(user_id: str, challenge: dict, store: dict) -> float:
    """Calculate recommendation score for a challenge"""
    weakness = weakness_signal(user_id, challenge, store)
    difficulty_fit = difficulty_fit_signal(user_id, challenge, store)

    return (
        WEIGHT_WEAKNESS * weakness +
        WEIGHT_DIFFICULTY_FIT * difficulty_fit
    )


def get_next_practice_challenge(user_id: str, store: dict | None = None) -> dict | None:
    """Get next challenge for practice mode using skill-based recommendation"""
    s = store if store is not None else load_store()
    all_challenges = get_challenges()
    # Consider any challenge that has been shown to the user as "seen" (whether answered correctly or not)
    seen_attempts = [a for a in s.get("challenge_attempts", []) if a.get("userId") == user_id]
    seen_ids = set(a.get("challengeId") for a in seen_attempts if a.get("challengeId"))

    # Get available challenges (exclude seen challenges so they are never shown twice in practice)
    available = [c for c in all_challenges if c["id"] not in seen_ids]

    if not available:
        # If the user has seen all challenges, allow repetition by returning a random
        # challenge instead of signaling "all completed". This lets users keep
        # practicing even after they've exhausted the pool once.
        return random.choice(all_challenges) if all_challenges else None

    # If user hasn't seen any challenges yet, pick random
    if not seen_ids:
        return random.choice(available)

    # Score each available challenge
    scored = [(calculate_challenge_score(user_id, c, s), c) for c in available]
    scored.sort(reverse=True, key=lambda x: x[0])

    return scored[0][1] if scored else None


def get_daily_challenge(store: dict | None = None) -> dict | None:
    """Get the daily challenge, picking a new one once per day"""
    s = store if store is not None else load_store()

    today_str = str(date.today())
    cache = s.get("daily_challenge_cache", {})

    # Check if we have a cached challenge for today
    if cache.get("date") == today_str and cache.get("challengeId"):
        return get_challenge(cache["challengeId"])

    # Pick a new random challenge from eligible ones
    all_challenges = get_challenges()
    eligible = [c for c in all_challenges if c.get("isDailyEligible", True)]

    if not eligible:
        return None

    daily_challenge = random.choice(eligible)

    # Cache it
    s["daily_challenge_cache"] = {
        "date": today_str,
        "challengeId": daily_challenge["id"],
    }
    save_store(s)

    return daily_challenge


def has_completed_challenge(user_id: str, challenge_id: str, store: dict | None = None) -> bool:
    """Check if user has completed a specific challenge"""
    s = store if store is not None else load_store()
    attempt = find_one(
        s["challenge_attempts"],
        userId=user_id,
        challengeId=challenge_id,
        isCorrect=True,
    )
    return attempt is not None
