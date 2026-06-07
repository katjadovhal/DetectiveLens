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
    {"level": 1, "title": "Internet Detective Level 1", "xp_required": 0},
    {"level": 2, "title": "Internet Detective Level 2", "xp_required": 300},
    {"level": 3, "title": "Internet Detective Level 3", "xp_required": 700},
    {"level": 4, "title": "Internet Detective Level 4", "xp_required": 1200},
    {"level": 5, "title": "Internet Detective Level 5", "xp_required": 2000},
]

XP_RULES = {
    "CHALLENGE_CORRECT": 100,
    "CHALLENGE_PARTIAL": 50,
    "DAILY_MISSION_BONUS": 100,
    "STREAK_BONUS": 25,
    "HINT_PENALTY": 10,
}

DEMO_USER_ID = "demo-user-id"
