import pytest

from app.constants import age_to_age_band, canonicalize_skill_id, canonicalize_skill_ids
from app.services.hint_engine import (
    HintAuthorizationError,
    SAFE_FALLBACKS,
    authorize_hint_stage,
    count_relevant_skill_attempts,
    generate_hint,
    normalize_locale,
    personalization_mode_for_attempts,
    resolve_age_band,
)


def _challenge(**overrides):
    base = {
        "id": "class-001",
        "slug": "class-001",
        "type": "fake_post",
        "skillCategoryIds": ["backgrounds", "content_authenticity"],
        "content": {
            "correctPostId": "B",
            "explanation": {
                "bullets": [
                    "Image B was generated using AI.",
                    "Image A is a real photograph.",
                ]
            },
        },
        "grounding": {
            "pre_answer_hint": "Compare background sharpness in both posts.",
            "stronger_hint": "Check for unusually smooth textures without picking a winner yet.",
            "answer_explanation": "Image B is AI-generated; Image A is real.",
            "detective_tip": "Compare texture consistency across the whole scene.",
        },
    }
    base.update(overrides)
    return base


def _profile(**overrides):
    base = {
        "id": "p1",
        "userId": "u1",
        "displayName": "Sam",
        "ageBand": "11_13",
    }
    base.update(overrides)
    return base


def test_age_banding():
    assert age_to_age_band(8) == "8_10"
    assert age_to_age_band(10) == "8_10"
    assert age_to_age_band(11) == "11_13"
    assert age_to_age_band(13) == "11_13"
    assert age_to_age_band(14) == "14_16"
    assert age_to_age_band(16) == "14_16"
    assert age_to_age_band(7) == "8_10"
    assert age_to_age_band(20) == "14_16"


def test_resolve_age_band_from_profile_and_default():
    assert resolve_age_band({"ageBand": "8_10"}) == "8_10"
    assert resolve_age_band({}) == "11_13"
    assert resolve_age_band(None, age=9) == "8_10"


def test_pre_answer_without_attempt_uses_grounding_not_explanation():
    result = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="pre_answer_hint",
        attempts=[],
    )
    assert result.source == "grounding"
    assert "Compare background" in result.text
    assert "Image B was generated" not in result.text
    assert result.personalizationMode == "neutral"


def test_stronger_hint_without_attempt_is_answer_neutral():
    result = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="stronger_hint",
        attempts=[],
    )
    assert "winner" in result.text or "smooth" in result.text
    assert "Image B was generated" not in result.text


def test_answer_explanation_denied_without_attempt():
    with pytest.raises(HintAuthorizationError):
        generate_hint(
            challenge=_challenge(),
            profile=_profile(),
            stage="answer_explanation",
            attempts=[],
        )


def test_answer_explanation_allowed_with_completed_attempt():
    attempts = [
        {
            "userId": "u1",
            "challengeId": "class-001",
            "attemptNumber": 1,
            "selectedAnswer": "A",
            "completedAt": "2026-01-01T00:00:00",
        }
    ]
    result = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="answer_explanation",
        attempts=attempts,
    )
    assert result.source == "grounding"
    assert "AI-generated" in result.text


def test_detective_tip_denied_without_attempt():
    with pytest.raises(HintAuthorizationError):
        generate_hint(
            challenge=_challenge(),
            profile=_profile(),
            stage="detective_tip",
            attempts=[],
        )


def test_detective_tip_allowed_with_attempt():
    attempts = [
        {
            "userId": "u1",
            "challengeId": "class-001",
            "attemptNumber": 1,
            "selectedAnswer": "B",
            "completedAt": "2026-01-01T00:00:00",
        }
    ]
    result = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="detective_tip",
        attempts=attempts,
    )
    assert result.source == "grounding"
    assert "texture" in result.text.lower()


def test_selected_option_and_attempt_number_mismatch_denied():
    attempts = [
        {
            "userId": "u1",
            "challengeId": "class-001",
            "attemptNumber": 2,
            "selectedAnswer": "A",
            "completedAt": "2026-01-01T00:00:00",
        }
    ]
    with pytest.raises(HintAuthorizationError):
        authorize_hint_stage(
            stage="answer_explanation",
            attempt=attempts[0],
            claimed_attempt_number=1,
        )
    with pytest.raises(HintAuthorizationError):
        authorize_hint_stage(
            stage="answer_explanation",
            attempt=attempts[0],
            claimed_selected_option="B",
        )


def test_legacy_challenge_pre_answer_uses_safe_fallback_not_bullets():
    challenge = _challenge(
        grounding=None,
        content={
            "correctPostId": "B",
            "explanation": {
                "bullets": [
                    "Image B was generated using AI.",
                    "Secret answer leak.",
                ]
            },
        },
    )
    result = generate_hint(
        challenge=challenge,
        profile=_profile(),
        stage="pre_answer_hint",
        attempts=[],
    )
    assert result.source == "curated_fallback"
    assert result.text == SAFE_FALLBACKS["pre_answer_hint"]
    assert "Secret answer leak" not in result.text
    assert "Image B was generated" not in result.text


def test_locale_falls_back_to_en():
    assert normalize_locale("de") == "en"
    assert normalize_locale("en-US") == "en"
    result = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="pre_answer_hint",
        attempts=[],
        locale="de",
    )
    assert result.locale == "en"


def test_skill_alias_and_canonical_attempt_counting():
    assert canonicalize_skill_id("blurred_background") == "backgrounds"
    assert canonicalize_skill_ids(["blurred_background", "shiny_texture", "backgrounds"]) == [
        "backgrounds",
        "content_authenticity",
    ]
    scores = [
        {"categoryId": "backgrounds", "attempts": 2},
        {"categoryId": "blurred_background", "attempts": 1},
        {"categoryId": "faces", "attempts": 9},
    ]
    total = count_relevant_skill_attempts(
        scores,
        ["blurred_background", "shiny_texture"],
    )
    # backgrounds(2) + aliased blurred_background(1) + content_authenticity(0)
    assert total == 3


def test_personalization_mode_threshold():
    assert personalization_mode_for_attempts(0) == "neutral"
    assert personalization_mode_for_attempts(2) == "neutral"
    assert personalization_mode_for_attempts(3) == "skill_practice"
    assert personalization_mode_for_attempts(10) == "skill_practice"
