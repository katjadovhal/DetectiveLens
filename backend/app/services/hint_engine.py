"""Hint engine: deterministic curated path + optional local Ollama (Phase 2)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from app.config import settings
from app.constants import (
    DEFAULT_AGE_BAND,
    VALID_AGE_BANDS,
    age_to_age_band,
    canonicalize_skill_id,
    canonicalize_skill_ids,
)

logger = logging.getLogger(__name__)

PRE_ANSWER_STAGES = frozenset({"pre_answer_hint", "stronger_hint"})
POST_ANSWER_STAGES = frozenset({"answer_explanation", "detective_tip"})

SAFE_FALLBACKS = {
    "pre_answer_hint": (
        "Compare both posts and note one detail that looks inconsistent "
        "with the rest of the scene."
    ),
    "stronger_hint": (
        "Focus on texture and edges in the background versus the main subject, "
        "without deciding which post is correct yet."
    ),
    "detective_tip": (
        "When images look polished, check whether small details stay consistent "
        "across the whole picture."
    ),
    "safe_generic": (
        "Keep comparing the posts carefully. Submit an answer to unlock "
        "the full explanation and detective tip."
    ),
}

PERSONALIZATION_ATTEMPT_THRESHOLD = 3

INTRO_TEMPLATES = {
    "neutral": "A useful check for this kind of challenge is",
    "skill_practice": "A skill that may be useful to practise is",
}

AGE_BAND_GUIDANCE = {
    "8_10": "Use short, simple sentences for children around ages 8–10.",
    "11_13": "Use clear, friendly language for ages 11–13.",
    "14_16": "Use concise teen-friendly language for ages 14–16.",
}

# Secondary safety net only — backend personalization policy is primary.
FORBIDDEN_PHRASE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\byou often\b",
        r"\byou always\b",
        r"\byour name\b",
        r"\byears old\b",
        r"\bage\s*\d+",
        r"\bI know you\b",
        r"\bbased on your history\b",
        r"\byou tend to\b",
    ]
]

PRE_ANSWER_LEAK_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bimage\s*[ab]\s+was\s+(generated|fake|ai)\b",
        r"\bcorrect\s+(answer|post|option)\b",
        r"\bthe\s+fake\s+(is|post)\b",
        r"\bchoose\s+(image\s*)?[ab]\b",
        r"\bpost\s*[ab]\s+is\s+(correct|fake|real|ai)\b",
    ]
]

MAX_MODEL_TEXT_LEN = 500
_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_MAX = 256

IntroTemplate = Literal["neutral", "skill_practice"]


class HintAuthorizationError(Exception):
    """Raised when a requested hint stage is not allowed for the current attempt state."""

    def __init__(self, message: str, code: str = "HINT_STAGE_FORBIDDEN"):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class HintResult:
    text: str
    stage: str
    source: str
    personalizationMode: str
    ageBand: str
    locale: str


def normalize_locale(locale: str | None) -> str:
    """MVP supports English only; unknown locales fall back to en."""
    if not locale:
        return "en"
    normalized = locale.strip().lower().replace("_", "-")
    if normalized == "en" or normalized.startswith("en-"):
        return "en"
    return "en"


def resolve_age_band(profile: dict | None, age: int | None = None) -> str:
    if profile and profile.get("ageBand") in VALID_AGE_BANDS:
        return profile["ageBand"]
    if age is not None:
        return age_to_age_band(age)
    return DEFAULT_AGE_BAND


def personalization_mode_for_attempts(relevant_attempt_count: int) -> IntroTemplate:
    """Backend-owned policy. The model must not choose personalization mode."""
    if relevant_attempt_count >= PERSONALIZATION_ATTEMPT_THRESHOLD:
        return "skill_practice"
    return "neutral"


def count_relevant_skill_attempts(
    skill_scores: list[dict],
    challenge_skill_ids: list[str],
) -> int:
    """Sum attempts for canonical skills shared with the challenge (merged by canonical id)."""
    canonical_challenge = set(canonicalize_skill_ids(challenge_skill_ids))
    if not canonical_challenge:
        return 0
    totals: dict[str, int] = {}
    for entry in skill_scores:
        canonical = canonicalize_skill_id(entry.get("categoryId"))
        if canonical and canonical in canonical_challenge:
            totals[canonical] = totals.get(canonical, 0) + int(entry.get("attempts") or 0)
    return sum(totals.values())


def resolve_personalization_mode(
    skill_scores: list[dict] | None,
    challenge_skill_ids: list[str] | None,
) -> IntroTemplate:
    relevant = count_relevant_skill_attempts(
        skill_scores or [],
        challenge_skill_ids or [],
    )
    return personalization_mode_for_attempts(relevant)


def hint_level_for_stage(stage: str, hint_level: int | None = None) -> int:
    if hint_level is not None:
        return hint_level
    if stage == "pre_answer_hint":
        return 1
    if stage == "stronger_hint":
        return 2
    return 0


def get_latest_completed_attempt(
    attempts: list[dict],
    *,
    user_id: str,
    challenge_id: str,
) -> dict | None:
    completed = [
        a
        for a in attempts
        if a.get("userId") == user_id
        and a.get("challengeId") == challenge_id
        and a.get("completedAt")
    ]
    if not completed:
        return None
    completed.sort(key=lambda a: a.get("completedAt") or "", reverse=True)
    return completed[0]


def authorize_hint_stage(
    *,
    stage: str,
    attempt: dict | None,
    claimed_attempt_number: int | None = None,
    claimed_selected_option: str | None = None,
) -> None:
    """Validate stage access against the stored attempt. Raises HintAuthorizationError."""
    if stage in PRE_ANSWER_STAGES:
        return

    if stage not in POST_ANSWER_STAGES:
        raise HintAuthorizationError(f"Unknown hint stage: {stage}", code="VALIDATION_ERROR")

    if not attempt or not attempt.get("completedAt"):
        raise HintAuthorizationError(
            "Complete a challenge attempt before requesting this hint stage."
        )

    if claimed_attempt_number is not None:
        stored_number = attempt.get("attemptNumber")
        if stored_number is not None and claimed_attempt_number != stored_number:
            raise HintAuthorizationError("attemptNumber does not match the stored attempt.")

    if claimed_selected_option is not None:
        stored_answer = attempt.get("selectedAnswer")
        if stored_answer is not None and claimed_selected_option != stored_answer:
            raise HintAuthorizationError("selectedOption does not match the stored attempt.")


def _explanation_text(challenge: dict) -> tuple[str, str] | None:
    grounding = challenge.get("grounding") or {}
    if grounding.get("answer_explanation"):
        return grounding["answer_explanation"], "grounding"

    content = challenge.get("content") or {}
    explanation = content.get("explanation") or {}
    bullets = explanation.get("bullets") or []
    title = explanation.get("title")
    parts = []
    if title:
        parts.append(str(title).strip())
    parts.extend(str(b).strip() for b in bullets if str(b).strip())
    if not parts:
        return None
    return " ".join(parts), "explanation"


def stage_grounded_text(challenge: dict, stage: str) -> tuple[str, str]:
    """Curated/deterministic text for a stage. Never uses explanation bullets for pre-answer."""
    grounding = challenge.get("grounding") or {}
    hint_fallbacks = challenge.get("hintFallbacks") or {}

    if stage == "answer_explanation":
        result = _explanation_text(challenge)
        if result:
            return result
        return SAFE_FALLBACKS["safe_generic"], "safe_generic"

    if stage == "pre_answer_hint":
        text = grounding.get("pre_answer_hint") or hint_fallbacks.get("pre_answer_hint")
        if text:
            source = "grounding" if grounding.get("pre_answer_hint") else "curated_fallback"
            return text, source
        return SAFE_FALLBACKS["pre_answer_hint"], "curated_fallback"

    if stage == "stronger_hint":
        text = grounding.get("stronger_hint") or hint_fallbacks.get("stronger_hint")
        if text:
            source = "grounding" if grounding.get("stronger_hint") else "curated_fallback"
            return text, source
        return SAFE_FALLBACKS["stronger_hint"], "curated_fallback"

    if stage == "detective_tip":
        text = grounding.get("detective_tip") or hint_fallbacks.get("detective_tip")
        if text:
            source = "grounding" if grounding.get("detective_tip") else "curated_fallback"
            return text, source
        return SAFE_FALLBACKS["detective_tip"], "curated_fallback"

    return SAFE_FALLBACKS["safe_generic"], "safe_generic"


# Back-compat alias used by tests
_stage_text = stage_grounded_text


def grounding_content_hash(challenge: dict) -> str:
    payload = {
        "grounding": challenge.get("grounding") or {},
        "hintFallbacks": challenge.get("hintFallbacks") or {},
        "id": challenge.get("id"),
        "slug": challenge.get("slug"),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_cache_key(
    *,
    challenge_id: str,
    grounding_hash: str,
    age_band: str,
    locale: str,
    stage: str,
    hint_level: int,
    model: str,
    prompt_version: str,
    personalization_mode: str = "neutral",
) -> str:
    return (
        f"hint:{challenge_id}:{grounding_hash}:{age_band}:{locale}:"
        f"{stage}:{hint_level}:{model}:{prompt_version}:{personalization_mode}"
    )


def apply_personalization_stem(text: str, *, mode: IntroTemplate, stage: str) -> str:
    """
    Prefix backend-owned intro stems for detective tips.
    The model must not choose the mode; this enforces the policy on curated copy too.
    """
    if stage != "detective_tip" or not text:
        return text
    stem = INTRO_TEMPLATES[mode]
    stripped = text.strip()
    if stripped.lower().startswith(stem.lower()):
        return stripped
    # Lowercase the first letter of the grounded sentence when joining to the stem.
    rest = stripped[0].lower() + stripped[1:] if stripped else stripped
    return f"{stem} {rest}"


def cache_get(key: str) -> dict[str, Any] | None:
    if not settings.hint_cache_enabled:
        return None
    return _CACHE.get(key)


def cache_set(key: str, value: dict[str, Any]) -> None:
    if not settings.hint_cache_enabled:
        return
    if len(_CACHE) >= _CACHE_MAX and key not in _CACHE:
        # Drop an arbitrary oldest-inserted key (CPython 3.7+ insertion order).
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[key] = value


def clear_hint_cache() -> None:
    _CACHE.clear()


def intro_template_for_mode(mode: IntroTemplate) -> str:
    return INTRO_TEMPLATES[mode]


def build_model_messages(
    *,
    stage: str,
    grounded_text: str,
    age_band: str,
    mode: IntroTemplate,
) -> list[dict[str, str]]:
    intro = intro_template_for_mode(mode)
    age_note = AGE_BAND_GUIDANCE.get(age_band, AGE_BAND_GUIDANCE[DEFAULT_AGE_BAND])
    stage_rules = {
        "pre_answer_hint": (
            "Write a short pre-answer observation hint. "
            "Do not reveal which post is correct or fake."
        ),
        "stronger_hint": (
            "Write a slightly more specific but still answer-neutral observation hint. "
            "Do not reveal which post is correct or fake."
        ),
        "answer_explanation": (
            "Rewrite the grounded explanation clearly for the learner. "
            "Stay faithful to the grounded facts."
        ),
        "detective_tip": (
            "Write a short transferable detective tip based on the grounded strategy. "
            "Do not make personal claims about the learner."
        ),
    }
    system = (
        "You are DetectiveLens, a kids media-literacy coach. "
        "Respond with JSON only: {\"text\": \"...\"}. "
        "English only. Do not invent facts beyond the grounded content. "
        "Never include the learner's name or exact age. "
        "Never decide personalization mode; follow the required opening stem exactly."
    )
    user = (
        f"Stage: {stage}\n"
        f"Age guidance: {age_note}\n"
        f"Required opening stem (use this idea; you may age-adapt the rest): \"{intro} ...\"\n"
        f"Personalization mode (already decided by the server): {mode}\n"
        f"Stage rule: {stage_rules.get(stage, 'Write a short helpful tip.')}\n"
        f"Grounded content to adapt:\n{grounded_text}\n"
        "Return JSON with key text only."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def parse_model_json(raw: str) -> str | None:
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    # Strip common markdown fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    value = data.get("text")
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_model_text(text: str, *, stage: str, mode: IntroTemplate) -> bool:
    if not text or not text.strip():
        return False
    if len(text) > MAX_MODEL_TEXT_LEN:
        return False
    lowered = text.lower()
    for pattern in FORBIDDEN_PHRASE_PATTERNS:
        if pattern.search(text):
            return False
    if stage in PRE_ANSWER_STAGES:
        for pattern in PRE_ANSWER_LEAK_PATTERNS:
            if pattern.search(text):
                return False
    # Soft check: skill_practice / neutral stems should not invent opposite personal claims.
    if mode == "neutral" and "a skill that may be useful to practise" in lowered:
        return False
    return True


def call_ollama_chat(
    messages: list[dict[str, str]],
    *,
    client: httpx.Client | None = None,
) -> str:
    """Call local Ollama /api/chat. Raises httpx errors on failure/timeout."""
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": settings.hint_model,
        "messages": messages,
        "stream": False,
        "format": "json",
    }
    timeout = httpx.Timeout(settings.hint_timeout_seconds)

    def _request(http_client: httpx.Client) -> str:
        response = http_client.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        body = response.json()
        message = body.get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("Ollama response missing message.content")
        return content

    if client is not None:
        return _request(client)

    with httpx.Client() as http_client:
        return _request(http_client)


def generate_with_model(
    *,
    stage: str,
    grounded_text: str,
    age_band: str,
    mode: IntroTemplate,
    client: httpx.Client | None = None,
) -> str | None:
    """Ask Ollama once, validate; on failure repair once; else return None for curated fallback."""
    messages = build_model_messages(
        stage=stage,
        grounded_text=grounded_text,
        age_band=age_band,
        mode=mode,
    )

    def _once(msgs: list[dict[str, str]]) -> str | None:
        try:
            raw = call_ollama_chat(msgs, client=client)
        except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
            logger.info("Ollama hint call failed: %s", exc)
            return None
        parsed = parse_model_json(raw)
        if not parsed:
            return None
        if not validate_model_text(parsed, stage=stage, mode=mode):
            return None
        return parsed

    first = _once(messages)
    if first:
        return first

    repair = messages + [
        {
            "role": "user",
            "content": (
                "Your previous reply was invalid. Return ONLY valid JSON like "
                '{"text":"..."} with a short English tip, no markdown, no personal claims.'
            ),
        }
    ]
    return _once(repair)


def generate_hint(
    *,
    challenge: dict,
    profile: dict,
    stage: str,
    attempts: list[dict],
    locale: str | None = "en",
    claimed_attempt_number: int | None = None,
    claimed_selected_option: str | None = None,
    skill_scores: list[dict] | None = None,
    hint_level: int | None = None,
    http_client: httpx.Client | None = None,
    use_model: bool | None = None,
) -> HintResult:
    """
    Authorize stage, then return curated text or (when enabled) an age-adapted model rewrite.

    use_model defaults to settings.hint_engine_enabled. App works without Ollama when false.
    """
    locale_norm = normalize_locale(locale)
    age_band = resolve_age_band(profile)
    attempt = get_latest_completed_attempt(
        attempts,
        user_id=profile["userId"],
        challenge_id=challenge["id"],
    )

    authorize_hint_stage(
        stage=stage,
        attempt=attempt,
        claimed_attempt_number=claimed_attempt_number,
        claimed_selected_option=claimed_selected_option,
    )

    mode = resolve_personalization_mode(
        skill_scores,
        challenge.get("skillCategoryIds"),
    )
    level = hint_level_for_stage(stage, hint_level)
    grounded_text, curated_source = stage_grounded_text(challenge, stage)

    model_enabled = settings.hint_engine_enabled if use_model is None else use_model
    model_name = settings.hint_model if model_enabled else "deterministic"
    g_hash = grounding_content_hash(challenge)
    key = build_cache_key(
        challenge_id=challenge["id"],
        grounding_hash=g_hash,
        age_band=age_band,
        locale=locale_norm,
        stage=stage,
        hint_level=level,
        model=model_name,
        prompt_version=settings.hint_prompt_version,
        personalization_mode=mode,
    )

    cached = cache_get(key)
    if cached:
        return HintResult(
            text=cached["text"],
            stage=stage,
            source=cached["source"],
            personalizationMode=mode,
            ageBand=age_band,
            locale=locale_norm,
        )

    text = grounded_text
    source = curated_source

    if model_enabled:
        model_text = generate_with_model(
            stage=stage,
            grounded_text=grounded_text,
            age_band=age_band,
            mode=mode,
            client=http_client,
        )
        if model_text:
            text = model_text
            source = "model"

    text = apply_personalization_stem(text, mode=mode, stage=stage)
    cache_set(key, {"text": text, "source": source})

    return HintResult(
        text=text,
        stage=stage,
        source=source,
        personalizationMode=mode,
        ageBand=age_band,
        locale=locale_norm,
    )
