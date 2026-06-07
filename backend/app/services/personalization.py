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
    if is_correct or challenge_type != "fake_post":
        return None

    if selected_answer == "B" and correct_answer == "A":
        return DetectiveTipResult(
            id="trusts_familiar_brands",
            message=(
                "You often trust posts from familiar brands without checking whether "
                "the content matches what they normally share."
            ),
            checklist=[
                "Check if the message fits the source",
                "Look for unusual or surprising claims",
                "Ask whether the post supports the account's goals",
            ],
        )

    return DetectiveTipResult(
        id="general_source_check",
        message=(
            "Remember: even verified accounts can share surprising content. "
            "Always check if it fits the source."
        ),
        checklist=[
            "Who posted this?",
            "Does the tone match the account?",
            "Would you expect this message from them?",
        ],
    )
