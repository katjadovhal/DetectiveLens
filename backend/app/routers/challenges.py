from fastapi import APIRouter, HTTPException

from app import repositories as repo
from app.schemas import SubmitFakePostAnswer
from app.schemas import HintRequest
from app.services.hint_engine.service import generate_hint

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("")
def list_challenges():
    challenges = repo.get_challenges()
    return {
        "challenges": [
            {
                "id": c["id"],
                "slug": c["slug"],
                "type": c["type"],
                "difficulty": c["difficulty"],
                "title": c["title"],
                "instruction": c["instruction"],
                "skillCategoryIds": c["skillCategoryIds"],
                "xpReward": c["xpReward"],
            }
            for c in challenges
        ]
    }


@router.get("/{challenge_id}")
def get_challenge(challenge_id: str):
    challenge = repo.get_challenge(challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Challenge not found", "statusCode": 404},
        )

    return {"challenge": repo.serialize_challenge(challenge, include_hints=True)}


@router.get("/users/{user_id}/next-practice")
def get_next_practice_challenge(user_id: str):
    """Get the next practice challenge for the user"""
    try:
        if repo.compute_challenge_completion(user_id)["allChallengesCompleted"]:
            return {
                **repo.all_challenges_completed_payload(),
                "challenge": None,
            }
        challenge = repo.get_next_practice_challenge(user_id)
        if not challenge:
            return {
                **repo.all_challenges_completed_payload(),
                "challenge": None,
            }
        return {"challenge": repo.serialize_challenge(challenge)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )


@router.get("/users/{user_id}/daily")
def get_daily_challenge(user_id: str):
    """Get today's daily challenge"""
    try:
        if repo.compute_challenge_completion(user_id)["allChallengesCompleted"]:
            return {
                **repo.all_challenges_completed_payload(),
                "challenge": None,
                "completed": True,
                "shareUrl": None,
            }

        challenge = repo.get_daily_challenge()
        if not challenge:
            raise HTTPException(
                status_code=404,
                detail={"error": "NOT_FOUND", "message": "No daily challenge available", "statusCode": 404},
            )

        completed = repo.has_completed_challenge(user_id, challenge["id"])
        return {
            "challenge": repo.serialize_challenge(challenge),
            "completed": completed,
            "shareUrl": f"https://detectivelens.app/challenge/{challenge['id']}?shared=true",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(e), "statusCode": 500},
        )


@router.post("/{challenge_id}/start/{user_id}")
def start_challenge(challenge_id: str, user_id: str):
    try:
        return repo.start_challenge(user_id, challenge_id)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Challenge not found", "statusCode": 404},
        )


@router.post("/{challenge_id}/hint")
async def request_hint(challenge_id: str, body: HintRequest):
    challenge = repo.get_challenge(challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Challenge not found", "statusCode": 404},
        )

    profile = repo.get_profile(body.userId)

    def record_view(session_id: str, hint_id: str) -> None:
        repo.record_hint_view(session_id, hint_id)

    try:
        response = await generate_hint(
            challenge,
            user_id=body.userId,
            stage=body.stage,
            session_id=body.sessionId,
            locale=body.locale,
            challenges=repo.get_challenges(),
            profile=profile,
            record_hint_view_fn=record_view,
        )
        return response.model_dump()
    except ValueError as exc:
        message = str(exc)
        status = 400
        if message == "Completed attempt required":
            status = 403
        raise HTTPException(
            status_code=status,
            detail={"error": "VALIDATION_ERROR", "message": message, "statusCode": status},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "SERVER_ERROR", "message": str(exc), "statusCode": 500},
        )


@router.post("/sessions/{session_id}/submit")
def submit_challenge(session_id: str, body: SubmitFakePostAnswer):
    try:
        return repo.submit_challenge(session_id, body.model_dump())
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Session not found", "statusCode": 404},
        )
