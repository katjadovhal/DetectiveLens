from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.constants import DEMO_USER_ID, XP_RULES
from app.database import get_db
from app.models import Challenge, ChallengeAttempt, User, XpSource, XpTransaction
from app.schemas import SubmitFakePostAnswer
from app.services.challenge_helpers import strip_correct_answer
from app.services.demo_user import ensure_demo_user
from app.services.personalization import get_detective_tip, get_weak_areas

router = APIRouter(prefix="/challenges", tags=["challenges"])


def _find_challenge(db: Session, challenge_id: str) -> Challenge | None:
    return (
        db.query(Challenge)
        .filter(
            ((Challenge.id == challenge_id) | (Challenge.slug == challenge_id)) & Challenge.active.is_(True)
        )
        .first()
    )


def _serialize_hint(hint) -> dict:
    return {
        "id": hint.id,
        "challengeId": hint.challenge_id,
        "order": hint.order,
        "question": hint.question,
        "content": hint.content,
        "skillCategoryId": hint.skill_category_id,
    }


def _serialize_challenge(challenge: Challenge, include_hints: bool = False) -> dict:
    data = {
        "id": challenge.id,
        "slug": challenge.slug,
        "type": challenge.type.value,
        "difficulty": challenge.difficulty.value,
        "title": challenge.title,
        "instruction": challenge.instruction,
        "content": strip_correct_answer(challenge.type, challenge.content),
        "skillCategoryIds": challenge.skill_category_ids,
        "xpReward": challenge.xp_reward,
        "isDailyEligible": challenge.is_daily_eligible,
    }
    if include_hints:
        data["hints"] = [_serialize_hint(h) for h in challenge.hints]
    return data


@router.get("")
def list_challenges(db: Session = Depends(get_db)):
    challenges = db.query(Challenge).filter(Challenge.active.is_(True)).all()
    return {
        "challenges": [
            {
                "id": c.id,
                "slug": c.slug,
                "type": c.type.value,
                "difficulty": c.difficulty.value,
                "title": c.title,
                "instruction": c.instruction,
                "skillCategoryIds": c.skill_category_ids,
                "xpReward": c.xp_reward,
            }
            for c in challenges
        ]
    }


@router.get("/{challenge_id}")
def get_challenge(challenge_id: str, db: Session = Depends(get_db)):
    challenge = (
        db.query(Challenge)
        .options(joinedload(Challenge.hints))
        .filter(
            ((Challenge.id == challenge_id) | (Challenge.slug == challenge_id)) & Challenge.active.is_(True)
        )
        .first()
    )
    if not challenge:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Challenge not found", "statusCode": 404})

    return {"challenge": _serialize_challenge(challenge, include_hints=True)}


@router.post("/{challenge_id}/start")
def start_challenge(challenge_id: str, db: Session = Depends(get_db)):
    challenge = _find_challenge(db, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Challenge not found", "statusCode": 404})

    user = ensure_demo_user(db)
    attempt = ChallengeAttempt(user_id=user.id, challenge_id=challenge.id)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {"sessionId": attempt.id, "challengeId": challenge.id}


@router.post("/sessions/{session_id}/submit")
def submit_challenge(session_id: str, body: SubmitFakePostAnswer, db: Session = Depends(get_db)):
    attempt = (
        db.query(ChallengeAttempt)
        .options(joinedload(ChallengeAttempt.challenge), joinedload(ChallengeAttempt.user).joinedload(User.profile))
        .filter(ChallengeAttempt.id == session_id)
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Session not found", "statusCode": 404})

    content = attempt.challenge.content
    correct_post_id = content.get("correctPostId")
    is_correct = body.selectedPostId == correct_post_id
    hint_penalty = body.hintsUsed * XP_RULES["HINT_PENALTY"]
    xp_earned = max(0, attempt.challenge.xp_reward - hint_penalty) if is_correct else 0

    attempt.selected_answer = body.selectedPostId
    attempt.is_correct = is_correct
    attempt.hints_used = body.hintsUsed
    attempt.time_spent_ms = body.timeSpentMs
    attempt.xp_earned = xp_earned
    attempt.completed_at = datetime.utcnow()

    if xp_earned > 0 and attempt.user.profile:
        profile = attempt.user.profile
        profile.total_xp += xp_earned
        profile.current_level_xp += xp_earned
        profile.last_challenge_id = attempt.challenge_id

        db.add(
            XpTransaction(
                user_id=attempt.user_id,
                amount=xp_earned,
                source=XpSource.challenge,
                reference_id=attempt.id,
            )
        )

    db.commit()

    tip = get_detective_tip(
        is_correct=is_correct,
        selected_answer=body.selectedPostId,
        correct_answer=correct_post_id,
        challenge_type=attempt.challenge.type.value,
    )

    explanation = content.get("explanation", {}).get("bullets", [])
    updated_xp = None
    if attempt.user.profile:
        updated_xp = attempt.user.profile.total_xp

    return {
        "attemptId": attempt.id,
        "isCorrect": is_correct,
        "selectedAnswer": body.selectedPostId,
        "correctAnswer": correct_post_id,
        "explanation": explanation,
        "xpEarned": xp_earned,
        "detectiveTip": tip.to_dict() if tip else None,
        "updatedXp": updated_xp,
    }
