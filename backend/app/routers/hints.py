from fastapi import APIRouter, HTTPException

from app import repositories as repo
from app.schemas_hint import HintRequest, HintResponse
from app.services.hint_engine import HintAuthorizationError, generate_hint
from app.storage import load_store

router = APIRouter(prefix="/challenges", tags=["hints"])


@router.post("/{challenge_id}/hint", response_model=HintResponse)
def request_hint(challenge_id: str, body: HintRequest):
    challenge = repo.get_challenge(challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Challenge not found", "statusCode": 404},
        )

    profile = repo.get_profile(body.userId)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Profile not found", "statusCode": 404},
        )

    store = load_store()
    skill_scores = [
        sc for sc in store.get("skill_scores", []) if sc.get("userId") == body.userId
    ]
    try:
        result = generate_hint(
            challenge=challenge,
            profile=profile,
            stage=body.stage,
            attempts=store.get("challenge_attempts", []),
            locale=body.locale,
            claimed_attempt_number=body.attemptNumber,
            claimed_selected_option=body.selectedOption,
            skill_scores=skill_scores,
            hint_level=body.hintLevel,
        )
    except HintAuthorizationError as exc:
        raise HTTPException(
            status_code=403,
            detail={"error": exc.code, "message": exc.message, "statusCode": 403},
        ) from exc

    return HintResponse(
        text=result.text,
        stage=result.stage,
        source=result.source,
        personalizationMode=result.personalizationMode,
        ageBand=result.ageBand,
        locale=result.locale,
    )
