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

CANONICAL_SKILL_IDS = {c["id"] for c in SKILL_CATEGORIES}

# Pilot / legacy challenge skill labels → canonical SKILL_CATEGORIES ids.
SKILL_ID_ALIASES = {
    "blurred_background": "backgrounds",
    "blurred_textures": "backgrounds",
    "shiny_texture": "content_authenticity",
    "waxy_perfect": "content_authenticity",
    "color": "content_authenticity",
    "emotions": "faces",
    "proportions": "faces",
    "functional": "evidence_evaluation",
    "sociocultural": "evidence_evaluation",
}

AGE_BAND_8_10 = "8_10"
AGE_BAND_11_13 = "11_13"
AGE_BAND_14_16 = "14_16"
DEFAULT_AGE_BAND = AGE_BAND_11_13
VALID_AGE_BANDS = {AGE_BAND_8_10, AGE_BAND_11_13, AGE_BAND_14_16}


def canonicalize_skill_id(skill_id: str | None) -> str | None:
    """Map a skill id to a canonical category id, or None if unknown."""
    if not skill_id:
        return None
    if skill_id in CANONICAL_SKILL_IDS:
        return skill_id
    mapped = SKILL_ID_ALIASES.get(skill_id)
    if mapped in CANONICAL_SKILL_IDS:
        return mapped
    return None


def canonicalize_skill_ids(skill_ids: list[str] | None) -> list[str]:
    """Deduplicate skill ids onto the canonical taxonomy (order preserved)."""
    if not skill_ids:
        return []
    seen: set[str] = set()
    result: list[str] = []
    for raw in skill_ids:
        canonical = canonicalize_skill_id(raw)
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


def age_to_age_band(age: int) -> str:
    """Derive a stored age band from a one-time onboarding age. Exact age is not persisted."""
    if age <= 10:
        return AGE_BAND_8_10
    if age <= 13:
        return AGE_BAND_11_13
    return AGE_BAND_14_16

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

# Legacy IDs mapped to current catalog (read/write normalization only).
AVATAR_ALIASES = {
    "detective-default": DEFAULT_AVATAR_ID,
}


def normalize_avatar_id(avatar_id: str | None) -> str:
    if not avatar_id:
        return DEFAULT_AVATAR_ID
    aliased = AVATAR_ALIASES.get(avatar_id, avatar_id)
    return aliased if aliased in AVATARS else DEFAULT_AVATAR_ID


DEMO_USER_ID = "demo-user-id"
