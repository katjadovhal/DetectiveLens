from copy import deepcopy


def strip_correct_answer(challenge_type: str, content: dict) -> dict:
    safe = deepcopy(content)
    ctype = challenge_type.value if hasattr(challenge_type, "value") else challenge_type

    if ctype == "fake_post":
        safe.pop("correctPostId", None)
        explanation = safe.pop("explanation", None)
        if explanation is not None:
            safe["explanation"] = {"bullets": []}
    elif ctype == "is_it_real":
        safe.pop("correctAnswer", None)
    elif ctype == "find_clues":
        hotspots = safe.get("hotspots", [])
        safe["hotspots"] = [
            {k: v for k, v in h.items() if k not in ("category", "label")}
            for h in hotspots
        ]

    return safe
