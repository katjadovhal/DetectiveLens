"""Local Ollama language adapter — required path with deterministic fallback."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings
from app.schemas import AdaptiveMessage
from app.services.hint_engine.age_language import apply_age_language
from app.services.hint_engine.presentation import default_presentation
from app.services.hint_engine.validation import to_adaptive_message, validate_message

logger = logging.getLogger(__name__)

_memory_cache: dict[str, AdaptiveMessage] = {}

AGE_GUIDANCE = {
    "8_10": (
        "Use one idea at a time, short active sentences, familiar concrete words. "
        "Optionally one simple guiding question. Main text about 25 words maximum."
    ),
    "11_13": (
        "Use one or two connected sentences and a brief reason for what to inspect. "
        "Main text about 45 words maximum."
    ),
    "14_16": (
        "Use more precise sentence structure and more detailed causal explanation. "
        "Uncertainty is appropriate where needed. Main text about 70 words maximum."
    ),
}


@dataclass
class AdaptResult:
    message: AdaptiveMessage
    fallback_used: bool


def _cache_key(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _build_fallback(approved: dict[str, Any], age_band: str, stage: str) -> AdaptiveMessage:
    # Even when Ollama is down, ages 8–10 must still see child-friendly wording.
    rewritten = apply_age_language(approved, age_band, stage)
    rewritten["presentation"] = default_presentation(age_band)
    return to_adaptive_message(rewritten, age_band)


async def _call_ollama(payload: dict[str, Any], age_band: str) -> AdaptiveMessage | None:
    if settings.hint_cache_enabled:
        key = _cache_key(payload)
        cached = _memory_cache.get(key)
        if cached:
            return cached

    system = (
        "You adapt detective training messages for children. "
        "Rewrite ONLY the approved content for the given ageBand. "
        "Adapt vocabulary, sentence construction, sentence length, "
        "ideas per sentence, amount of explanation, tone, and checklist wording. "
        "For ageBand 8_10: use only simple everyday words a young child knows. "
        "Avoid words like texture, surface, unusually, flawless, waxy, saturated, anatomy. "
        "Prefer words like look, skin, shiny, smooth, blurry, colour, size. "
        "Also choose a presentation preset that matches the age policy. "
        "Do not add facts, counts, diagnoses, or answer reveals. "
        "Never return HTML, CSS, JavaScript, font URLs, colours as CSS, or pixel values. "
        "Return JSON matching the AdaptiveMessage schema including presentation. "
        f"Age guidance: {AGE_GUIDANCE.get(age_band, AGE_GUIDANCE['11_13'])}"
    )
    user = json.dumps(payload)

    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    body = {
        "model": settings.hint_model,
        "stream": False,
        "think": False,
        "options": {"temperature": settings.hint_temperature},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "format": AdaptiveMessage.model_json_schema(),
    }

    try:
        async with httpx.AsyncClient(timeout=settings.hint_timeout_seconds) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "")
            parsed = json.loads(content)
            message = AdaptiveMessage.model_validate(parsed)
            if settings.hint_cache_enabled:
                _memory_cache[_cache_key(payload)] = message
            return message
    except Exception as exc:
        logger.warning("Ollama hint adaptation failed: %s", exc)
        return None


async def adapt_message_result(
    *,
    age_band: str,
    locale: str,
    stage: str,
    approved: dict[str, Any],
    pattern_ids: list[str],
    personalization_mode: str,
    interaction_summary: dict[str, Any],
    allowed_pattern_ids: list[str] | None = None,
    is_young: bool = False,
) -> AdaptResult:
    """Build fallback, attempt Ollama, validate, return model or fallback."""
    fallback = _build_fallback(approved, age_band, stage)
    allowed = allowed_pattern_ids if allowed_pattern_ids is not None else pattern_ids

    if not settings.hint_engine_enabled:
        return AdaptResult(message=fallback, fallback_used=True)

    payload = {
        "ageBand": age_band,
        "locale": locale,
        "stage": stage,
        "approvedTitle": approved["title"],
        "approvedText": approved["text"],
        "approvedChecklist": approved.get("checklist") or [],
        "patternIds": pattern_ids,
        "personalizationMode": personalization_mode,
        "interactionSummary": interaction_summary,
        "promptVersion": settings.hint_prompt_version,
        "defaultPresentation": default_presentation(age_band).model_dump(),
    }

    adapted = await _call_ollama(payload, age_band)
    if adapted is None:
        return AdaptResult(message=fallback, fallback_used=True)

    errors = validate_message(
        adapted,
        stage=stage,
        allowed_pattern_ids=allowed,
        age_band=age_band,
        is_young=is_young,
        approved_text=approved.get("text"),
    )
    if errors:
        logger.info("Hint adaptation validation failed: %s", errors)
        return AdaptResult(message=fallback, fallback_used=True)

    return AdaptResult(message=adapted, fallback_used=False)


async def adapt_message(
    *,
    age_band: str,
    locale: str,
    stage: str,
    approved: dict[str, Any],
    pattern_ids: list[str],
    personalization_mode: str,
    interaction_summary: dict[str, Any],
    allowed_pattern_ids: list[str] | None = None,
    is_young: bool = False,
) -> AdaptiveMessage:
    """Public adapter contract: always returns AdaptiveMessage."""
    result = await adapt_message_result(
        age_band=age_band,
        locale=locale,
        stage=stage,
        approved=approved,
        pattern_ids=pattern_ids,
        personalization_mode=personalization_mode,
        interaction_summary=interaction_summary,
        allowed_pattern_ids=allowed_pattern_ids,
        is_young=is_young,
    )
    return result.message


adapt_with_ollama = adapt_message
