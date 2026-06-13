from fastapi import APIRouter

from app import repositories as repo

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/{user_id}")
@router.get("")
def get_home(user_id: str | None = None):
    return repo.get_home_data()
