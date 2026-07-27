import asyncio

from app.config import settings
from app.schemas import AdaptiveMessage
from app.services.hint_engine.ollama_adapter import adapt_message, adapt_message_result
from app.services.hint_engine.presentation import default_presentation


def test_adapt_message_returns_adaptive_message_on_fallback(monkeypatch):
    monkeypatch.setattr(settings, "hint_engine_enabled", False)
    approved = {
        "title": "Detective Clue",
        "text": "Compare both images carefully.",
        "checklist": ["Look at edges"],
        "tone": "supportive",
        "pattern_ids": ["color"],
        "evidence_claim": None,
        "reveals_answer": False,
    }
    message = asyncio.run(
        adapt_message(
            age_band="11_13",
            locale="en",
            stage="pre_answer_hint",
            approved=approved,
            pattern_ids=["color"],
            personalization_mode="insufficient_data",
            interaction_summary={},
        )
    )
    assert isinstance(message, AdaptiveMessage)
    assert message.presentation == default_presentation("11_13")
    assert message.reveals_answer is False


def test_adapt_message_result_marks_fallback(monkeypatch):
    monkeypatch.setattr(settings, "hint_engine_enabled", False)
    approved = {
        "title": "Why?",
        "text": "Review the clues that helped identify the answer.",
        "checklist": [],
        "tone": "neutral",
        "pattern_ids": [],
        "evidence_claim": None,
        "reveals_answer": False,
    }
    result = asyncio.run(
        adapt_message_result(
            age_band="8_10",
            locale="en",
            stage="answer_explanation",
            approved=approved,
            pattern_ids=[],
            personalization_mode="neutral",
            interaction_summary={},
            allowed_pattern_ids=[],
        )
    )
    assert result.fallback_used is True
    assert result.message.presentation.preset == "young_reader"


def test_eight_year_old_fallback_is_child_friendly(monkeypatch):
    monkeypatch.setattr(settings, "hint_engine_enabled", False)
    approved = {
        "title": "Detective Clue",
        "text": (
            "Look closely at skin and smooth surfaces. "
            "Compare the surface textures in both images."
        ),
        "checklist": ["Look for natural skin texture"],
        "tone": "supportive",
        "pattern_ids": ["waxy_perfect", "shiny_texture"],
        "evidence_claim": None,
        "reveals_answer": False,
    }
    message = asyncio.run(
        adapt_message(
            age_band="8_10",
            locale="en",
            stage="pre_answer_hint",
            approved=approved,
            pattern_ids=["waxy_perfect", "shiny_texture"],
            personalization_mode="insufficient_data",
            interaction_summary={},
        )
    )
    lowered = message.text.lower()
    assert "texture" not in lowered
    assert "surfaces" not in lowered
    assert "smooth" in lowered or "skin" in lowered
    assert len(message.text.split()) <= 25
