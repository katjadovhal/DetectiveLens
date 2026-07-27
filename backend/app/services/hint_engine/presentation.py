"""Age-band presentation presets for adaptive messages."""

from __future__ import annotations

from app.schemas import MessagePresentation

# Allowed presentation values per age band (inclusive of defaults).
AGE_PRESENTATION_POLICY: dict[str, dict[str, set[str]]] = {
    "8_10": {
        "preset": {"young_reader"},
        "font_style": {"rounded"},
        "font_scale": {"large"},
        "line_spacing": {"relaxed"},
        "content_width": {"narrow"},
        "emphasis_style": {"keywords"},
    },
    "11_13": {
        "preset": {"middle_reader"},
        "font_style": {"rounded", "standard"},
        "font_scale": {"medium", "large"},
        "line_spacing": {"relaxed", "normal"},
        "content_width": {"medium"},
        "emphasis_style": {"keywords", "none"},
    },
    "14_16": {
        "preset": {"advanced_reader"},
        "font_style": {"standard"},
        "font_scale": {"medium", "compact"},
        "line_spacing": {"normal", "relaxed"},
        "content_width": {"wide", "medium"},
        "emphasis_style": {"keywords", "none"},
    },
}

DEFAULT_PRESENTATION: dict[str, MessagePresentation] = {
    "8_10": MessagePresentation(
        preset="young_reader",
        font_style="rounded",
        font_scale="large",
        line_spacing="relaxed",
        content_width="narrow",
        emphasis_style="keywords",
    ),
    "11_13": MessagePresentation(
        preset="middle_reader",
        font_style="rounded",
        font_scale="medium",
        line_spacing="relaxed",
        content_width="medium",
        emphasis_style="keywords",
    ),
    "14_16": MessagePresentation(
        preset="advanced_reader",
        font_style="standard",
        font_scale="medium",
        line_spacing="normal",
        content_width="wide",
        emphasis_style="none",
    ),
}

PRESET_TO_CSS_CLASS = {
    "young_reader": "adaptive-message--young",
    "middle_reader": "adaptive-message--middle",
    "advanced_reader": "adaptive-message--advanced",
}


def default_presentation(age_band: str) -> MessagePresentation:
    return DEFAULT_PRESENTATION.get(age_band, DEFAULT_PRESENTATION["11_13"]).model_copy()


def validate_presentation(presentation: MessagePresentation, age_band: str) -> list[str]:
    policy = AGE_PRESENTATION_POLICY.get(age_band, AGE_PRESENTATION_POLICY["11_13"])
    errors: list[str] = []
    checks = {
        "preset": presentation.preset,
        "font_style": presentation.font_style,
        "font_scale": presentation.font_scale,
        "line_spacing": presentation.line_spacing,
        "content_width": presentation.content_width,
        "emphasis_style": presentation.emphasis_style,
    }
    for field, value in checks.items():
        if value not in policy[field]:
            errors.append(f"presentation_invalid:{field}:{value}")
    return errors
