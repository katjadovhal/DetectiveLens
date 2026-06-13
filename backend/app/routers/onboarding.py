from fastapi import APIRouter, HTTPException

from app import repositories as repo
from app.schemas import OnboardingComplete

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/welcome")
def get_welcome():
    return {
        "title": "Hey Detective!",
        "subtitle": "The Internet is full of tricks. Let's learn how to spot them.",
        "keyValue": "Become an Internet Detective and learn to spot misinformation and AI-generated content.",
    }


@router.post("/complete")
def complete_onboarding(body: OnboardingComplete):
    return repo.complete_onboarding(body.level)
