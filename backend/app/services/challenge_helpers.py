from copy import deepcopy

from app.models import ChallengeType


def strip_correct_answer(challenge_type: ChallengeType | str, content: dict) -> dict:
    safe = deepcopy(content)
    ctype = challenge_type.value if isinstance(challenge_type, ChallengeType) else challenge_type

    if ctype == "fake_post":
        safe.pop("correctPostId", None)
    elif ctype == "is_it_real":
        safe.pop("correctAnswer", None)
    elif ctype == "find_clues":
        hotspots = safe.get("hotspots", [])
        safe["hotspots"] = [
            {k: v for k, v in h.items() if k not in ("category", "label")}
            for h in hotspots
        ]

    return safe
