from fastapi import APIRouter, HTTPException

from app import repositories as repo
from app.schemas import OnboardingComplete, CreateUser

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/welcome")
def get_welcome():
    return {
        "title": "Welcome to DetectiveLens!",
        "subtitle": "Some pictures lie. Learn to spot the cues and catch them all.",
        "keyValue": "Learn to detect misinformation and AI-generated content.",
    }


@router.post("/create-user")
def create_user(body: CreateUser):
    try:
        return repo.create_user(body.model_dump())
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "VALIDATION_ERROR", "message": str(e), "statusCode": 400},
        )
