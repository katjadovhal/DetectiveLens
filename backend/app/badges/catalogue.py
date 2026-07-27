"""Central Badge catalogue — metadata only; no challenge/pattern data."""

from __future__ import annotations

from typing import Any

# Project-assumption thresholds (documented in design-decisions.md).
FIRST_CASE_TARGET = 1
CASE_SOLVER_TARGET = 10
CLUE_STRATEGIST_TARGET = 3
COMEBACK_TARGET = 1
PATTERN_EXPLORER_TARGET = 4
DETAIL_DETECTIVE_MIN_RELEVANT = 5
DETAIL_DETECTIVE_RECENT_WINDOW = 5
DETAIL_DETECTIVE_RECENT_CORRECT = 4

BADGE_CATALOGUE: list[dict[str, Any]] = [
    {
        "id": "first_case",
        "title": "First Case",
        "description": "Complete your first challenge.",
        "icon": "🕵️",
        "category": "milestone",
        "target": FIRST_CASE_TARGET,
        "whyItMatters": "Starting your first case begins your detective training.",
        "approvedUnlockReason": "You completed your first challenge.",
        "approvedNotification": "You earned First Case.",
    },
    {
        "id": "case_solver",
        "title": "Case Solver",
        "description": "Complete 10 challenges.",
        "icon": "📁",
        "category": "milestone",
        "target": CASE_SOLVER_TARGET,
        "whyItMatters": "Practice across many cases builds investigation habits.",
        "approvedUnlockReason": "You completed 10 challenges.",
        "approvedNotification": "You earned Case Solver.",
    },
    {
        "id": "clue_strategist",
        "title": "Clue Strategist",
        "description": "Use a clue and then solve 3 challenges correctly.",
        "icon": "🔍",
        "category": "learning_strategy",
        "target": CLUE_STRATEGIST_TARGET,
        "whyItMatters": "Using clues can help you learn an investigation strategy.",
        "approvedUnlockReason": "You used a clue and then solved 3 challenges correctly.",
        "approvedNotification": "You earned Clue Strategist.",
    },
    {
        "id": "comeback_detective",
        "title": "Comeback Detective",
        "description": "Improve on a case type you missed earlier.",
        "icon": "🔄",
        "category": "recovery",
        "target": COMEBACK_TARGET,
        "whyItMatters": "Trying again after a miss is an important learning skill.",
        "approvedUnlockReason": (
            "You later solved a challenge that shared investigation clues "
            "with one you missed earlier."
        ),
        "approvedNotification": "You earned Comeback Detective.",
    },
    {
        "id": "pattern_explorer",
        "title": "Pattern Explorer",
        "description": "Meet at least 4 different clue types across completed challenges.",
        "icon": "🧭",
        "category": "breadth",
        "target": PATTERN_EXPLORER_TARGET,
        "whyItMatters": "Seeing many clue types helps you compare carefully.",
        "approvedUnlockReason": "Your completed challenges covered at least 4 clue types.",
        "approvedNotification": "You earned Pattern Explorer.",
    },
    {
        "id": "detail_detective",
        "title": "Detail Detective",
        "description": (
            "Complete 5 challenges linked to one clue type, "
            "with at least 4 of your last 5 correct."
        ),
        "icon": "🔎",
        "category": "depth",
        "target": DETAIL_DETECTIVE_MIN_RELEVANT,
        "whyItMatters": "Careful practice with one clue type builds attention to detail.",
        "approvedUnlockReason": (
            "You completed 5 challenges linked to one clue type, "
            "with strong recent accuracy."
        ),
        "approvedNotification": "You earned Detail Detective.",
    },
]


def get_badge_def(badge_id: str) -> dict[str, Any] | None:
    for badge in BADGE_CATALOGUE:
        if badge["id"] == badge_id:
            return badge
    return None


def all_badge_ids() -> list[str]:
    return [b["id"] for b in BADGE_CATALOGUE]
