import asyncio

from app import repositories as repo
from app.services.hint_engine.service import generate_hint


def _profile():
    return repo.get_profile("user-1")


def test_pre_answer_hint_without_ollama(temp_store):
    challenges = repo.get_challenges()
    challenge = repo.get_challenge("monkey-001")
    start = repo.start_challenge("user-1", "monkey-001")

    response = asyncio.run(
        generate_hint(
            challenge,
            user_id="user-1",
            stage="pre_answer_hint",
            session_id=start["sessionId"],
            locale="en",
            challenges=challenges,
            profile=_profile(),
            record_hint_view_fn=lambda sid, hid: repo.record_hint_view(sid, hid),
        )
    )

    assert response.title
    assert response.text
    assert response.revealsAnswer is False
    assert response.fallbackUsed is True
    assert response.presentation is not None
    assert response.presentation.preset in (
        "young_reader",
        "middle_reader",
        "advanced_reader",
    )
    assert "correct answer" not in response.text.lower()


def test_post_answer_requires_completed_attempt(temp_store):
    challenges = repo.get_challenges()
    challenge = repo.get_challenge("monkey-001")
    start = repo.start_challenge("user-1", "monkey-001")

    try:
        asyncio.run(
            generate_hint(
                challenge,
                user_id="user-1",
                stage="answer_explanation",
                session_id=start["sessionId"],
                locale="en",
                challenges=challenges,
                profile=_profile(),
            )
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Completed attempt required"


def test_answer_explanation_after_submit(temp_store):
    challenges = repo.get_challenges()
    challenge = repo.get_challenge("monkey-001")
    start = repo.start_challenge("user-1", "monkey-001")
    content = challenge["content"]
    wrong_id = next(
        p["id"] for p in content["posts"] if p["id"] != content["correctPostId"]
    )
    repo.submit_challenge(
        start["sessionId"],
        {"selectedPostId": wrong_id, "hintsUsed": 0},
    )

    response = asyncio.run(
        generate_hint(
            challenge,
            user_id="user-1",
            stage="answer_explanation",
            session_id=start["sessionId"],
            locale="en",
            challenges=challenges,
            profile=_profile(),
        )
    )

    assert response.title == "Why?"
    assert len(response.text) > 10
    assert response.fallbackUsed is True
