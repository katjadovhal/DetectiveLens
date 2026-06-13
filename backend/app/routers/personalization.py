from fastapi import APIRouter

from app import repositories as repo

router = APIRouter(prefix="/personalization", tags=["personalization"])


@router.get("/{user_id}/skill-profile")
@router.get("/skill-profile")
def get_skill_profile(user_id: str | None = None):
    return repo.get_skill_profile()


@router.get("/{user_id}/weak-areas")
@router.get("/weak-areas")
def get_weak_areas_route(user_id: str | None = None):
    return repo.get_weak_areas_data()


@router.get("/{user_id}/recommendations")
@router.get("/recommendations")
def get_recommendations(user_id: str | None = None):
    return repo.get_recommendations()
