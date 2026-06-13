from fastapi import APIRouter, HTTPException

from app import repositories as repo
from app.schemas import SubmitFakePostAnswer

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


@router.post("/{challenge_id}/start")
def start_challenge(challenge_id: str):
    try:
        return repo.start_challenge(challenge_id)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Challenge not found", "statusCode": 404},
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
