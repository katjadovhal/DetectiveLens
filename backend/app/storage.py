import json
import threading
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from app.config import settings

_lock = threading.Lock()


def _default_store() -> dict:
    return {
        "users": [],
        "profiles": [],
        "skill_scores": [],
        "challenge_attempts": [],
        "xp_transactions": [],
        "detective_tips": [],
        "daily_missions": [],
    }


def _store_path() -> Path:
    return Path(settings.data_dir) / "store.json"


def load_store() -> dict:
    path = _store_path()
    if not path.exists():
        return _default_store()
    return json.loads(path.read_text())


def save_store(store: dict) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2, default=str))


def with_store(fn):
    def wrapper(*args, **kwargs):
        with _lock:
            store = load_store()
            result = fn(store, *args, **kwargs)
            save_store(store)
            return result

    return wrapper


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def find_one(items: list, **filters) -> dict | None:
    for item in items:
        if all(item.get(k) == v for k, v in filters.items()):
            return item
    return None


def find_by_id_or_slug(challenges: list[dict], challenge_id: str) -> dict | None:
    for c in challenges:
        if c["id"] == challenge_id or c["slug"] == challenge_id:
            return c
    return None


def deep_get(store: dict) -> dict:
    return deepcopy(store)
