"""Optional local Ollama language adapter."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.schemas import AdaptiveMessage

logger = logging.getLogger(__name__)

_memory_cache: dict[str, AdaptiveMessage] = {}


def _cache_key(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


async def adapt_with_ollama(
    *,
    age_band: str,
    locale: str,
    stage: str,
    approved: dict[str, Any],
    pattern_ids: list[str],
    personalization_mode: str,
    interaction_summary: dict[str, Any],
) -> AdaptiveMessage | None:
    if not settings.hint_engine_enabled:
        return None

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
    }

    if settings.hint_cache_enabled:
        key = _cache_key(payload)
        cached = _memory_cache.get(key)
        if cached:
            return cached

    system = (
        "You adapt detective training messages for children. "
        "Rewrite ONLY the approved content for the given ageBand. "
        "Do not add facts, counts, diagnoses, or answer reveals. "
        "Return JSON matching the schema."
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
