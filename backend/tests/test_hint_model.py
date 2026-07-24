import json

import httpx
import pytest

from app.services.hint_engine import (
    SAFE_FALLBACKS,
    apply_personalization_stem,
    build_cache_key,
    build_model_messages,
    clear_hint_cache,
    generate_hint,
    generate_with_model,
    grounding_content_hash,
    intro_template_for_mode,
    parse_model_json,
    validate_model_text,
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


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_hint_cache()
    yield
    clear_hint_cache()


def test_parse_model_json_accepts_object_and_fenced():
    assert parse_model_json('{"text":"Hello detectives."}') == "Hello detectives."
    assert parse_model_json('```json\n{"text":"Clue time."}\n```') == "Clue time."
    assert parse_model_json("not json") is None
    assert parse_model_json('{"text":""}') is None


def test_validate_rejects_forbidden_and_pre_answer_leaks():
    assert validate_model_text(
        "Compare the background edges carefully.",
        stage="pre_answer_hint",
        mode="neutral",
    )
    assert not validate_model_text(
        "You often miss background blur.",
        stage="detective_tip",
        mode="neutral",
    )
    assert not validate_model_text(
        "Image A was generated using AI.",
        stage="pre_answer_hint",
        mode="neutral",
    )


def test_intro_templates_are_backend_controlled():
    assert intro_template_for_mode("neutral").startswith("A useful check")
    assert intro_template_for_mode("skill_practice").startswith("A skill that may be useful")
    messages = build_model_messages(
        stage="detective_tip",
        grounded_text="Check texture consistency.",
        age_band="11_13",
        mode="skill_practice",
    )
    joined = " ".join(m["content"] for m in messages)
    assert "skill_practice" in joined
    assert "A skill that may be useful to practise" in joined
    assert "Sam" not in joined
    assert "years old" not in joined


def test_cache_key_format():
    key = build_cache_key(
        challenge_id="class-001",
        grounding_hash="abc123",
        age_band="11_13",
        locale="en",
        stage="pre_answer_hint",
        hint_level=1,
        model="qwen3:4b",
        prompt_version="v1",
        personalization_mode="neutral",
    )
    assert key == "hint:class-001:abc123:11_13:en:pre_answer_hint:1:qwen3:4b:v1:neutral"


def test_grounding_hash_changes_with_content():
    a = grounding_content_hash(_challenge())
    b = grounding_content_hash(
        _challenge(grounding={"pre_answer_hint": "Different hint text."})
    )
    assert a != b


def _mock_transport(payload_text: str, *, fail_times: int = 0):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] <= fail_times:
            return httpx.Response(500, json={"error": "boom"})
        return httpx.Response(
            200,
            json={"message": {"content": json.dumps({"text": payload_text})}},
        )

    return httpx.MockTransport(handler), calls


def test_model_success_returns_source_model(monkeypatch):
    monkeypatch.setattr("app.services.hint_engine.settings.hint_engine_enabled", True)
    monkeypatch.setattr("app.services.hint_engine.settings.hint_cache_enabled", True)
    transport, calls = _mock_transport(
        "A useful check for this kind of challenge is comparing background edges."
    )
    client = httpx.Client(transport=transport)

    result = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="pre_answer_hint",
        attempts=[],
        use_model=True,
        http_client=client,
    )
    assert result.source == "model"
    assert "background" in result.text.lower()
    assert calls["n"] == 1

    # Second call should hit cache (no extra Ollama call).
    result2 = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="pre_answer_hint",
        attempts=[],
        use_model=True,
        http_client=client,
    )
    assert result2.text == result.text
    assert calls["n"] == 1


def test_model_timeout_falls_back_to_curated(monkeypatch):
    monkeypatch.setattr("app.services.hint_engine.settings.hint_engine_enabled", True)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="pre_answer_hint",
        attempts=[],
        use_model=True,
        http_client=client,
    )
    assert result.source == "grounding"
    assert "Compare background" in result.text


def test_invalid_model_output_repairs_once_then_falls_back(monkeypatch):
    monkeypatch.setattr("app.services.hint_engine.settings.hint_engine_enabled", True)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        # Always invalid JSON content
        return httpx.Response(200, json={"message": {"content": "NOT_JSON"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    text = generate_with_model(
        stage="pre_answer_hint",
        grounded_text="Compare backgrounds.",
        age_band="11_13",
        mode="neutral",
        client=client,
    )
    assert text is None
    assert calls["n"] == 2  # initial + one repair


def test_disabled_engine_never_calls_ollama(monkeypatch):
    monkeypatch.setattr("app.services.hint_engine.settings.hint_engine_enabled", False)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"message": {"content": '{"text":"nope"}'}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="pre_answer_hint",
        attempts=[],
        http_client=client,
    )
    assert calls["n"] == 0
    assert result.source == "grounding"


def test_legacy_fallback_unchanged_when_model_fails(monkeypatch):
    monkeypatch.setattr("app.services.hint_engine.settings.hint_engine_enabled", True)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no ollama", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_hint(
        challenge=_challenge(grounding=None),
        profile=_profile(),
        stage="pre_answer_hint",
        attempts=[],
        use_model=True,
        http_client=client,
    )
    assert result.text == SAFE_FALLBACKS["pre_answer_hint"]
    assert result.source == "curated_fallback"


def test_detective_tip_applies_skill_practice_stem():
    attempts = [
        {
            "userId": "u1",
            "challengeId": "class-001",
            "attemptNumber": 1,
            "selectedAnswer": "A",
            "completedAt": "2026-01-01T00:00:00",
        }
    ]
    scores = [
        {"categoryId": "backgrounds", "attempts": 2},
        {"categoryId": "content_authenticity", "attempts": 2},
    ]
    result = generate_hint(
        challenge=_challenge(),
        profile=_profile(),
        stage="detective_tip",
        attempts=attempts,
        skill_scores=scores,
        use_model=False,
    )
    assert result.personalizationMode == "skill_practice"
    assert result.text.startswith("A skill that may be useful to practise is")


def test_apply_personalization_stem_idempotent():
    stemmed = apply_personalization_stem(
        "A useful check for this kind of challenge is comparing textures.",
        mode="neutral",
        stage="detective_tip",
    )
    assert stemmed.count("A useful check for this kind of challenge is") == 1
