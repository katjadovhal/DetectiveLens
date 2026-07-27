from app.schemas import AdaptiveMessage
from app.services.hint_engine.validation import validate_message


def test_pre_answer_rejects_answer_reveal():
    message = AdaptiveMessage(
        title="Clue",
        text="The correct answer is image B because it is fake.",
        checklist=[],
        tone="supportive",
        pattern_ids=["color"],
        reveals_answer=False,
    )
    errors = validate_message(
        message,
        stage="pre_answer_hint",
        allowed_pattern_ids=["color"],
        age_band="11_13",
    )
    assert any("pre_answer_forbidden" in e or "correct answer" in e for e in errors)


def test_pre_answer_accepts_safe_clue():
    message = AdaptiveMessage(
        title="Detective Clue",
        text="Compare lighting and shadows on both images before you choose.",
        checklist=["Look at edges"],
        tone="supportive",
        pattern_ids=["color"],
        reveals_answer=False,
    )
    errors = validate_message(
        message,
        stage="pre_answer_hint",
        allowed_pattern_ids=["color"],
        age_band="11_13",
    )
    assert errors == []


def test_forbidden_personalization_phrase_rejected():
    message = AdaptiveMessage(
        title="Tip",
        text="You often trust posts from familiar brands.",
        checklist=[],
        tone="supportive",
        pattern_ids=["color"],
        reveals_answer=False,
    )
    errors = validate_message(
        message,
        stage="detective_tip",
        allowed_pattern_ids=["color"],
        age_band="11_13",
    )
    assert any("forbidden_phrase" in e for e in errors)
