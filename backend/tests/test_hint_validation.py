from app.schemas import AdaptiveMessage, MessagePresentation
from app.services.hint_engine.presentation import default_presentation, validate_presentation
from app.services.hint_engine.validation import validate_message


def _presentation(age_band="11_13"):
    return default_presentation(age_band)


def test_pre_answer_rejects_answer_reveal():
    message = AdaptiveMessage(
        title="Clue",
        text="The correct answer is image B because it is fake.",
        checklist=[],
        tone="supportive",
        pattern_ids=["color"],
        reveals_answer=False,
        presentation=_presentation(),
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
        presentation=_presentation(),
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
        presentation=_presentation(),
    )
    errors = validate_message(
        message,
        stage="detective_tip",
        allowed_pattern_ids=["color"],
        age_band="11_13",
    )
    assert any("forbidden_phrase" in e for e in errors)


def test_presentation_rejects_wrong_age_band_preset():
    presentation = MessagePresentation(
        preset="advanced_reader",
        font_style="standard",
        font_scale="compact",
        line_spacing="normal",
        content_width="wide",
        emphasis_style="none",
    )
    errors = validate_presentation(presentation, "8_10")
    assert any("presentation_invalid:preset" in e for e in errors)


def test_default_presentation_valid_for_each_band():
    for band in ("8_10", "11_13", "14_16"):
        assert validate_presentation(default_presentation(band), band) == []
