import json
import random
from copy import deepcopy
from datetime import datetime, date
from pathlib import Path

from app.constants import (
    DIFFICULTY_MAP,
    HINT_PENALTY,
    LEVELS,
    WEIGHT_WEAKNESS,
    WEIGHT_DIFFICULTY_FIT,
    normalize_avatar_id,
    require_unlocked_avatar,
)
from app.hq_shop import HQ_SHOP_BY_ID
from app.badges.engine import evaluate_badge_states, find_newly_unlocked
from app.badges.wording import build_unlock_payload, resolve_age_band
from app.services.challenge_helpers import strip_correct_answer
from app.services.hint_engine.analytics import build_pattern_summaries
from app.services.hint_engine.deterministic import build_detective_tip
from app.services.hint_engine.policy import select_personalization_mode
from app.services.hint_engine.service import derive_age_band, validate_onboarding_age
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


def _category_name(category_id: str) -> str:
    return category_id.replace("_", " ").title()


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


def get_skill_categories() -> list[dict]:
    """Return the skill categories used by challenge JSON files."""
    categories = []
    seen = set()
    for challenge in _load_challenges_from_files():
        for category_id in challenge.get("skillCategoryIds", []):
            if category_id in seen:
                continue
            seen.add(category_id)
            categories.append(
                {
                    "id": category_id,
                    "name": _category_name(category_id),
                }
            )
    return categories


def ensure_skill_scores(store: dict, user_id: str) -> None:
    existing = {
        score["categoryId"]
        for score in store.get("skill_scores", [])
        if score.get("userId") == user_id
    }
    for skill in get_skill_categories():
        if skill["id"] in existing:
            continue
        store["skill_scores"].append({
            "id": new_id(),
            "userId": user_id,
            "categoryId": skill["id"],
            "score": 0,
            "attempts": 0,
            "correct": 0,
        })
        existing.add(skill["id"])


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

    completion = compute_challenge_completion(user_id, s)
    daily_challenge = None
    if not completion["allChallengesCompleted"]:
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
        "challengeCompletion": completion,
    }


ALL_CHALLENGES_COMPLETED_STATUS = "all_challenges_completed"
ALL_CHALLENGES_COMPLETED_MESSAGE = "You have completed all available challenges."
ALL_CHALLENGES_COMPLETED_NEXT_ROUTE = "/detective-hq"


def all_challenges_completed_payload() -> dict:
    """Safe expected-state payload for practice/daily when catalogue is finished."""
    return {
        "status": ALL_CHALLENGES_COMPLETED_STATUS,
        "message": ALL_CHALLENGES_COMPLETED_MESSAGE,
        "nextRoute": ALL_CHALLENGES_COMPLETED_NEXT_ROUTE,
    }


def compute_challenge_completion(user_id: str, store: dict | None = None) -> dict:
    """Derive catalogue completion from available challenges + completed attempts.

    A challenge counts as completed for this user when there is at least one attempt
    with completedAt set whose challengeId is in the current catalogue.
    """
    s = store if store is not None else load_store()
    available_ids = {c["id"] for c in get_challenges() if c.get("id")}
    if not available_ids:
        return {
            "allChallengesCompleted": False,
            "completedChallenges": 0,
            "totalChallenges": 0,
            "remainingChallenges": 0,
        }

    completed_ids = {
        attempt.get("challengeId")
        for attempt in s.get("challenge_attempts", [])
        if attempt.get("userId") == user_id
        and attempt.get("completedAt")
        and attempt.get("challengeId") in available_ids
    }

    completed_count = len(completed_ids)
    total_count = len(available_ids)
    remaining = total_count - completed_count
    return {
        "allChallengesCompleted": completed_ids == available_ids,
        "completedChallenges": completed_count,
        "totalChallenges": total_count,
        "remainingChallenges": remaining,
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
                "hqOwnedItemIds": [],
                "ageBand": "11_13",
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
            "settings": profile["settings"],
            "hqOwnedItemIds": list(profile.get("hqOwnedItemIds") or []),
            "ageBand": profile.get("ageBand", "11_13"),
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
        # Enforce XP unlock gates server-side.
        profile["avatarId"] = require_unlocked_avatar(
            body["avatarId"],
            profile.get("totalXp", 0),
        )
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
def purchase_hq_item(store: dict, user_id: str, item_id: str) -> dict:
    """Spend profile totalXp on a Detective HQ shop item (no duplicate buys)."""
    profile = get_profile(user_id, store)
    if not profile:
        raise ValueError("Profile not found")

    item = HQ_SHOP_BY_ID.get(item_id)
    if not item:
        raise ValueError("Unknown shop item")

    owned = list(profile.get("hqOwnedItemIds") or [])
    if item_id in owned:
        raise ValueError("Already owned")

    price = int(item["price"])
    total_xp = int(profile.get("totalXp") or 0)
    if total_xp < price:
        raise ValueError("Not enough XP")

    profile["totalXp"] = total_xp - price
    profile["currentLevelXp"] = max(0, int(profile.get("currentLevelXp") or 0) - price)
    owned.append(item_id)
    profile["hqOwnedItemIds"] = owned

    return {
        "itemId": item_id,
        "totalXp": profile["totalXp"],
        "currentLevelXp": profile["currentLevelXp"],
        "hqOwnedItemIds": owned,
        "message": "Purchase successful",
    }


@with_store
def create_user(store: dict, body: dict) -> dict:
    """Create a new user during onboarding"""
    # Check if username already exists
    existing = find_one(store["users"], username=body["username"])
    if existing:
        raise ValueError("Username already exists")

    user_id = new_id()
    age = validate_onboarding_age(int(body.get("age", 11)))
    avatar_id = require_unlocked_avatar(body.get("avatarId"), 0)
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
        "avatarId": avatar_id,
        "displayName": body["username"],
        "currentLevel": 1,
        "totalXp": 0,
        "currentLevelXp": 0,
        "dailyStreak": 0,
        "onboardingCompleted": True,
        "colorBlindness": body.get("colorBlindness", False),
        "lastChallengeId": None,
        "lastChallengeProgress": None,
        "settings": {"notifications": True, "sound": True, "privacy": False},
        "hqOwnedItemIds": [],
        "ageBand": derive_age_band(age),
        "youngReader": False,
    }
    store["profiles"].append(profile)

    # Initialize skill scores from challenge JSON category ids.
    ensure_skill_scores(store, user_id)

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

    attempt = {
        "id": new_id(),
        "userId": user_id,
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
def record_hint_view(store: dict, session_id: str, hint_id: str) -> dict:
    attempt = find_one(store["challenge_attempts"], id=session_id)
    if not attempt or attempt.get("completedAt"):
        raise ValueError("Invalid session")

    viewed = list(attempt.get("hintsViewed") or [])
    if hint_id not in viewed:
        viewed.append(hint_id)
    attempt["hintsViewed"] = viewed
    attempt["hintsUsed"] = len(viewed)
    return {"hintsViewed": viewed, "hintsUsed": attempt["hintsUsed"]}


async def get_learning_insights_data(user_id: str) -> dict:
    from app.services.hint_engine.service import get_learning_insights

    profile = get_profile(user_id)
    return await get_learning_insights(user_id, get_challenges(), profile=profile)


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
    hint_penalty = body.get("hintsUsed", 0) * HINT_PENALTY
    xp_earned = max(0, challenge["xpReward"] - hint_penalty) if is_correct else 0

    attempt["selectedAnswer"] = body["selectedPostId"]
    attempt["isCorrect"] = is_correct
    viewed_count = len(attempt.get("hintsViewed") or [])
    attempt["hintsUsed"] = max(int(body.get("hintsUsed", 0)), viewed_count)
    attempt["xpEarned"] = xp_earned
    attempt["completedAt"] = now_iso()

    if body.get("timeSpentMs") is not None:
        attempt["timeSpentMs"] = body.get("timeSpentMs")
    else:
        started = attempt.get("startedAt")
        if started:
            try:
                start = datetime.fromisoformat(started)
                end = datetime.fromisoformat(attempt["completedAt"])
                attempt["timeSpentMs"] = max(0, int((end - start).total_seconds() * 1000))
            except ValueError:
                attempt["timeSpentMs"] = None
        else:
            attempt["timeSpentMs"] = None

    profile = get_profile(attempt["userId"], store)
    leveled_up = False
    updated_level = None
    if profile:
        profile["totalXp"] += xp_earned
        profile["currentLevelXp"] += xp_earned
        leveled_up = apply_level_up(profile)
        updated_level = profile["currentLevel"]
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

    detective_tip = None
    if not is_correct:
        pattern_ids = challenge.get("skillCategoryIds") or []
        summaries = build_pattern_summaries(
            attempt["userId"],
            store["challenge_attempts"],
            {challenge["id"]: challenge},
            pattern_ids,
        )
        policy = select_personalization_mode(summaries, pattern_ids)
        tip_payload = build_detective_tip(
            pattern_ids,
            policy.personalization_mode,
            policy.evidence_count,
        )
        detective_tip = {
            "id": policy.personalization_mode,
            "message": tip_payload["text"],
            "checklist": tip_payload["checklist"],
        }

    explanation = content.get("explanation", {}).get("bullets", [])
    updated_xp = profile["totalXp"] if profile else None

    newly_unlocked = apply_badge_unlocks(
        store,
        user_id=attempt["userId"],
        profile=profile,
    )

    return {
        "attemptId": attempt["id"],
        "isCorrect": is_correct,
        "selectedAnswer": body["selectedPostId"],
        "correctAnswer": correct_post_id,
        "explanation": explanation,
        "xpEarned": xp_earned,
        "detectiveTip": detective_tip,
        "updatedXp": updated_xp,
        "leveledUp": leveled_up,
        "currentLevel": updated_level,
        "newlyUnlockedBadges": newly_unlocked,
    }


def apply_badge_unlocks(store: dict, *, user_id: str, profile: dict | None) -> list[dict]:
    """Evaluate badges after a completed attempt; persist unlocks + notifications."""
    store.setdefault("user_badges", [])
    store.setdefault("notifications", [])

    challenges = get_challenges()
    newly = find_newly_unlocked(
        user_id=user_id,
        attempts=store.get("challenge_attempts", []),
        challenges=challenges,
        user_badges=store.get("user_badges", []),
    )
    if not newly:
        return []

    age_band = resolve_age_band(profile)
    earned_at = now_iso()
    payloads: list[dict] = []

    for badge in newly:
        badge_id = badge["id"]
        if _has_user_badge(store, user_id, badge_id):
            continue

        store["user_badges"].append(
            {
                "id": new_id(),
                "userId": user_id,
                "badgeId": badge_id,
                "earnedAt": earned_at,
            }
        )

        payload = build_unlock_payload(badge, age_band=age_band)
        payload["earnedAt"] = earned_at
        payload["notificationId"] = None
        payloads.append(payload)

        if _has_badge_unlock_notification(store, user_id, badge_id):
            continue

        note_id = new_id()
        store["notifications"].append(
            {
                "id": note_id,
                "userId": user_id,
                "type": "badge_unlocked",
                "badgeId": badge_id,
                "title": "New badge unlocked!",
                "message": payload["message"],
                "createdAt": earned_at,
                "readAt": None,
            }
        )
        payload["notificationId"] = note_id

    return payloads


def _has_user_badge(store: dict, user_id: str, badge_id: str) -> bool:
    return find_one(store.get("user_badges", []), userId=user_id, badgeId=badge_id) is not None


def _has_badge_unlock_notification(store: dict, user_id: str, badge_id: str) -> bool:
    return any(
        n.get("userId") == user_id
        and n.get("type") == "badge_unlocked"
        and n.get("badgeId") == badge_id
        for n in store.get("notifications", [])
    )


def backfill_missing_badge_notifications(store: dict, user_id: str, profile: dict | None = None) -> int:
    """Idempotent optional helper: one notification per earned badge that lacks one.

    Not called from profile load or submit. Returns number of notifications created.
    """
    store.setdefault("user_badges", [])
    store.setdefault("notifications", [])
    age_band = resolve_age_band(profile)
    created = 0
    for row in list(store["user_badges"]):
        if row.get("userId") != user_id:
            continue
        badge_id = row.get("badgeId")
        if not badge_id or _has_badge_unlock_notification(store, user_id, badge_id):
            continue
        from app.badges.catalogue import get_badge_def

        badge = get_badge_def(badge_id)
        if not badge:
            continue
        payload = build_unlock_payload(badge, age_band=age_band)
        store["notifications"].append(
            {
                "id": new_id(),
                "userId": user_id,
                "type": "badge_unlocked",
                "badgeId": badge_id,
                "title": "New badge unlocked!",
                "message": payload["message"],
                "createdAt": row.get("earnedAt") or now_iso(),
                "readAt": None,
            }
        )
        created += 1
    return created


def get_user_badges_data(user_id: str) -> dict:
    store = load_store()
    store.setdefault("user_badges", [])
    badges = evaluate_badge_states(
        user_id=user_id,
        attempts=store.get("challenge_attempts", []),
        challenges=get_challenges(),
        user_badges=store.get("user_badges", []),
    )
    return {"badges": badges}


@with_store
def list_notifications(store: dict, user_id: str) -> dict:
    store.setdefault("notifications", [])
    items = [n for n in store["notifications"] if n.get("userId") == user_id]
    items.sort(key=lambda n: n.get("createdAt") or "", reverse=True)
    unread = sum(1 for n in items if not n.get("readAt"))
    return {
        "notifications": items,
        "unreadCount": unread,
    }


@with_store
def mark_notification_read(store: dict, user_id: str, notification_id: str) -> dict:
    store.setdefault("notifications", [])
    note = find_one(store["notifications"], id=notification_id, userId=user_id)
    if not note:
        raise ValueError("Notification not found")
    if not note.get("readAt"):
        note["readAt"] = now_iso()
    items = [n for n in store["notifications"] if n.get("userId") == user_id]
    unread = sum(1 for n in items if not n.get("readAt"))
    return {"notification": note, "unreadCount": unread}


@with_store
def mark_all_notifications_read(store: dict, user_id: str) -> dict:
    store.setdefault("notifications", [])
    now = now_iso()
    for note in store["notifications"]:
        if note.get("userId") == user_id and not note.get("readAt"):
            note["readAt"] = now
    items = [n for n in store["notifications"] if n.get("userId") == user_id]
    return {"notifications": items, "unreadCount": 0}


def get_skill_profile(user_id: str, store: dict | None = None) -> dict:
    s = store if store is not None else load_store()
    ensure_skill_scores(s, user_id)
    categories = {c["id"]: c for c in get_skill_categories()}
    scores = [
        sc
        for sc in s["skill_scores"]
        if sc.get("userId") == user_id and sc.get("categoryId") in categories
    ]

    if not scores:
        return {"skillProfile": []}

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
    ensure_skill_scores(s, user_id)
    category_ids = {c["id"] for c in get_skill_categories()}
    scores = [
        sc
        for sc in s["skill_scores"]
        if sc.get("userId") == user_id and sc.get("categoryId") in category_ids
    ]
    mapped = [
        {
            "categoryId": sc["categoryId"],
            "score": sc["score"],
            "attempts": sc["attempts"],
            "correct": sc["correct"],
        }
        for sc in scores
    ]
    weak = get_weak_areas(mapped) if mapped else []
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
    """Update user skill profile after a challenge"""
    skill_categories = challenge.get("skillCategoryIds", [])
    if not skill_categories:
        return

    n = len(skill_categories)
    delta = (1 / n) if correct else -(1 / n)

    for skill_id in skill_categories:
        score_entry = find_one(store["skill_scores"], userId=user_id, categoryId=skill_id)
        if not score_entry:
            score_entry = {
                "id": new_id(),
                "userId": user_id,
                "categoryId": skill_id,
                "score": 0,
                "attempts": 0,
                "correct": 0,
            }
            store["skill_scores"].append(score_entry)
        score_entry["score"] = clamp(score_entry["score"] + delta, -1, 1)
        score_entry["attempts"] = score_entry.get("attempts", 0) + 1
        if correct:
            score_entry["correct"] = score_entry.get("correct", 0) + 1


def weakness_signal(user_id: str, challenge: dict, store: dict) -> float:
    """Calculate weakness signal for challenge recommendation"""
    skill_categories = challenge.get("skillCategoryIds", [])
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
    skill_categories = challenge.get("skillCategoryIds", [])
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
    if compute_challenge_completion(user_id, s)["allChallengesCompleted"]:
        return None

    all_challenges = get_challenges()
    # Consider any challenge that has been shown to the user as "seen" (whether answered correctly or not)
    seen_attempts = [a for a in s.get("challenge_attempts", []) if a.get("userId") == user_id]
    seen_ids = set(a.get("challengeId") for a in seen_attempts if a.get("challengeId"))

    # Get available challenges (exclude seen challenges so they are never shown twice in practice)
    available = [c for c in all_challenges if c["id"] not in seen_ids]

    if not available:
        # If the user has seen all challenges but has not completed the full catalogue
        # (e.g. started without submitting), allow repetition so practice stays available.
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
