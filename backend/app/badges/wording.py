"""Age-adaptive Badge wording — LLM may rewrite approved text only."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.badges.catalogue import get_badge_def
from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_AGE_BAND = "11_13"
VALID_AGE_BANDS = {"8_10", "11_13", "14_16"}

AGE_GUIDANCE = {
    "8_10": "Use short simple sentences and everyday words for young children.",
    "11_13": "Use clear friendly sentences with a brief reason.",
    "14_16": "Use precise supportive wording with a short causal explanation.",
}

UNSAFE_RE = re.compile(r"(</?[a-z][^>]*>|javascript:|url\()", re.I)


def resolve_age_band(profile: dict | None) -> str:
    if profile and profile.get("ageBand") in VALID_AGE_BANDS:
        return profile["ageBand"]
    return DEFAULT_AGE_BAND


def approved_unlock_message(badge_id: str) -> str:
    definition = get_badge_def(badge_id)
    if not definition:
        return "You unlocked a new badge."
    return definition["approvedNotification"]


def approved_unlock_reason(badge_id: str) -> str:
    definition = get_badge_def(badge_id)
    if not definition:
        return "You met the badge requirement."
    return definition["approvedUnlockReason"]


def _validate_adapted(text: str, *, age_band: str) -> bool:
    if not text or not isinstance(text, str):
        return False
    cleaned = text.strip()
    if len(cleaned) < 3 or len(cleaned) > 220:
        return False
    if UNSAFE_RE.search(cleaned):
        return False
    words = re.findall(r"\b[\w']+\b", cleaned)
    limit = {"8_10": 28, "11_13": 40, "14_16": 55}.get(age_band, 40)
    if len(words) > limit:
        return False
    lowered = cleaned.lower()
    forbidden = ("you are bad", "you always fail", "confirmation bias")
    return not any(p in lowered for p in forbidden)


def _call_ollama(payload: dict[str, Any]) -> str | None:
    if not settings.hint_engine_enabled:
        return None
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    body = {
        "model": settings.hint_model,
        "stream": False,
        "format": "json",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Rewrite the approved badge message for the given ageBand. "
                    "Do not change the meaning or invent achievements. "
                    "Never use HTML or CSS. Return JSON {\"text\":\"...\"}."
                ),
            },
            {"role": "user", "content": json.dumps(payload)},
        ],
    }
    try:
        with httpx.Client(timeout=settings.hint_timeout_seconds) as client:
            response = client.post(url, json=body)
            response.raise_for_status()
            content = (response.json().get("message") or {}).get("content") or ""
            parsed = json.loads(content)
            text = parsed.get("text") if isinstance(parsed, dict) else None
            return text if isinstance(text, str) else None
    except Exception as exc:
        logger.info("Badge wording Ollama failed: %s", exc)
        return None


def adapt_badge_message(
    *,
    age_band: str,
    badge_title: str,
    approved_reason: str,
    context: str = "badge_unlock",
) -> str:
    """Return age-adapted text, or the deterministic approved message on failure."""
    band = age_band if age_band in VALID_AGE_BANDS else DEFAULT_AGE_BAND
    fallback = approved_reason
    if context == "badge_unlock_notification":
        fallback = approved_reason

    payload = {
        "ageBand": band,
        "badgeTitle": badge_title,
        "approvedReason": approved_reason,
        "context": context,
        "guidance": AGE_GUIDANCE.get(band, AGE_GUIDANCE[DEFAULT_AGE_BAND]),
    }
    adapted = _call_ollama(payload)
    if adapted and _validate_adapted(adapted, age_band=band):
        return adapted.strip()
    return fallback


def build_unlock_payload(
    badge: dict[str, Any],
    *,
    age_band: str,
) -> dict[str, Any]:
    reason = approved_unlock_reason(badge["id"])
    notification = approved_unlock_message(badge["id"])
    adapted_reason = adapt_badge_message(
        age_band=age_band,
        badge_title=badge["title"],
        approved_reason=reason,
        context="badge_unlock",
    )
    adapted_notification = adapt_badge_message(
        age_band=age_band,
        badge_title=badge["title"],
        approved_reason=notification,
        context="badge_unlock_notification",
    )
    return {
        "id": badge["id"],
        "title": badge["title"],
        "description": badge.get("description"),
        "icon": badge.get("icon"),
        "category": badge.get("category"),
        "status": "unlocked",
        "progress": badge.get("target"),
        "target": badge.get("target"),
        "whyItMatters": badge.get("whyItMatters"),
        "message": adapted_notification,
        "reason": adapted_reason,
    }
