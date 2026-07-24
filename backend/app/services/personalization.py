from dataclasses import dataclass


@dataclass
class DetectiveTipResult:
    id: str
    message: str
    checklist: list[str]

    def to_dict(self) -> dict:
        return {"id": self.id, "message": self.message, "checklist": self.checklist}


def get_weak_areas(scores: list[dict], threshold: float = 60) -> list[dict]:
    filtered = [s for s in scores if s["score"] < threshold or s["attempts"] == 0]
    return sorted(filtered, key=lambda s: s["score"])


def get_detective_tip(
    *,
    is_correct: bool,
    selected_answer: str,
    correct_answer: str,
    challenge_type: str,
) -> DetectiveTipResult | None:
    """Legacy submit-path tip. Neutral copy only — no personal claims about the learner."""
    if is_correct or challenge_type != "fake_post":
        return None

    return DetectiveTipResult(
        id="general_visual_check",
        message=(
            "A useful check for this kind of challenge is whether small details "
            "stay consistent across the whole picture."
        ),
        checklist=[
            "Compare texture and edges in both posts",
            "Look for details that feel too perfect or inconsistent",
            "Ask whether the whole scene could work in real life",
        ],
    )
