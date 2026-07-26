SKILL_CATEGORIES = [
    {"id": "source_verification", "name": "Source Verification", "parent_group": "misinformation", "library_topic_id": None},
    {"id": "content_authenticity", "name": "Content Authenticity", "parent_group": "misinformation", "library_topic_id": None},
    {"id": "evidence_evaluation", "name": "Evidence Evaluation", "parent_group": "media_literacy", "library_topic_id": None},
    {"id": "faces", "name": "Faces", "parent_group": "ai_artifacts", "library_topic_id": "faces"},
    {"id": "hands", "name": "Hands", "parent_group": "ai_artifacts", "library_topic_id": "hands"},
    {"id": "backgrounds", "name": "Backgrounds", "parent_group": "ai_artifacts", "library_topic_id": "backgrounds"},
    {"id": "text", "name": "Text", "parent_group": "ai_artifacts", "library_topic_id": "text"},
    {"id": "lighting_shadows", "name": "Lighting & Shadows", "parent_group": "ai_artifacts", "library_topic_id": "lighting-shadows"},
]

LEVELS = [
    {"level": 1, "title": "Internet Detective Level 1", "xp_to_advance": 500},
    {"level": 2, "title": "Internet Detective Level 2", "xp_to_advance": 400},
    {"level": 3, "title": "Internet Detective Level 3", "xp_to_advance": 500},
    {"level": 4, "title": "Internet Detective Level 4", "xp_to_advance": 800},
    {"level": 5, "title": "Internet Detective Level 5", "xp_to_advance": None},
]

XP_RULES = {
    "CHALLENGE_CORRECT": 100,
    "CHALLENGE_PARTIAL": 50,
    "DAILY_MISSION_BONUS": 100,
    "STREAK_BONUS": 25,
    "HINT_PENALTY": 10,
}

DIFFICULTY_MAP = {
    "easy": -0.5,
    "medium": 0,
    "hard": 0.5,
}

WEIGHT_WEAKNESS = 0.7
WEIGHT_DIFFICULTY_FIT = 0.3

DEFAULT_AVATAR_ID = "avatar-detective-1"

AVATARS = [
    "avatar-detective-1",
    "avatar-detective-2",
    "avatar-detective-3",
    "avatar-detective-4",
]

# XP required to select each avatar (0 = always available).
AVATAR_UNLOCK_XP = {
    "avatar-detective-1": 0,
    "avatar-detective-2": 0,
    "avatar-detective-3": 400,  # Dog
    "avatar-detective-4": 600,  # Cat
}

# Legacy IDs mapped to current catalog (read/write normalization only).
AVATAR_ALIASES = {
    "detective-default": DEFAULT_AVATAR_ID,
}


def normalize_avatar_id(avatar_id: str | None) -> str:
    if not avatar_id:
        return DEFAULT_AVATAR_ID
    aliased = AVATAR_ALIASES.get(avatar_id, avatar_id)
    return aliased if aliased in AVATARS else DEFAULT_AVATAR_ID


def is_avatar_unlocked(avatar_id: str | None, total_xp: int | float | None) -> bool:
    normalized = normalize_avatar_id(avatar_id)
    required = AVATAR_UNLOCK_XP.get(normalized, 0)
    return int(total_xp or 0) >= required


def require_unlocked_avatar(avatar_id: str | None, total_xp: int | float | None) -> str:
    """Return a normalized avatar id or raise ValueError if still locked."""
    normalized = normalize_avatar_id(avatar_id)
    if not is_avatar_unlocked(normalized, total_xp):
        needed = AVATAR_UNLOCK_XP.get(normalized, 0)
        raise ValueError(f"Avatar unlocks at {needed} XP")
    return normalized


DEMO_USER_ID = "demo-user-id"
