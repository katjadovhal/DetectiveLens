from app.services.hint_engine.analytics import PatternInteractionSummary
from app.services.hint_engine.policy import select_personalization_mode, select_practice_challenge


def _summary(pattern_id: str, **kwargs) -> PatternInteractionSummary:
    base = PatternInteractionSummary(pattern_id=pattern_id)
    for key, value in kwargs.items():
        setattr(base, key, value)
    return base


def test_insufficient_data_when_few_attempts():
    summaries = {
        "color": _summary("color", relevant_attempts=1, correct=0, incorrect=1, accuracy=0.0),
    }
    result = select_personalization_mode(summaries, ["color"])
    assert result.personalization_mode == "insufficient_data"


def test_practice_support_when_repeated_miss():
    summaries = {
        "color": _summary(
            "color",
            relevant_attempts=4,
            correct=1,
            incorrect=3,
            accuracy=0.25,
            repeated_associated_miss=True,
        ),
    }
    result = select_personalization_mode(summaries, ["color"])
    assert result.personalization_mode == "practice_support"
    assert result.practice_pattern == "color"


def test_select_practice_challenge_skips_current_and_recent():
    challenges = [
        {"id": "a", "skillCategoryIds": ["color"], "difficulty": "easy"},
        {"id": "b", "skillCategoryIds": ["color"], "difficulty": "medium"},
        {"id": "c", "skillCategoryIds": ["anatomy"], "difficulty": "easy"},
    ]
    attempts = [
        {
            "userId": "user-1",
            "challengeId": "b",
            "completedAt": "2099-01-01T12:00:00",
        },
    ]
    picked = select_practice_challenge(
        "user-1",
        "current",
        "color",
        attempts,
        challenges,
        "medium",
    )
    assert picked == "a"
