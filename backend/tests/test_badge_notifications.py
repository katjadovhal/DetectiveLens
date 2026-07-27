"""Badge unlock notification persistence helpers."""

from app.badges.catalogue import get_badge_def
from app.repositories import (
    apply_badge_unlocks,
    backfill_missing_badge_notifications,
)


def test_apply_badge_unlocks_creates_one_notification_per_new_badge(monkeypatch):
    first = get_badge_def("first_case")
    strategist = get_badge_def("clue_strategist")
    assert first and strategist

    monkeypatch.setattr(
        "app.repositories.find_newly_unlocked",
        lambda **_kwargs: [first, strategist],
    )
    monkeypatch.setattr("app.repositories.get_challenges", lambda: [])

    store = {"user_badges": [], "notifications": [], "challenge_attempts": []}
    profile = {"ageBand": "8_10"}
    unlocked = apply_badge_unlocks(store, user_id="u1", profile=profile)

    assert len(unlocked) == 2
    assert {b["id"] for b in unlocked} == {"first_case", "clue_strategist"}
    assert all(b.get("notificationId") for b in unlocked)

    notes = [n for n in store["notifications"] if n["userId"] == "u1"]
    assert len(notes) == 2
    assert all(n["title"] == "New badge unlocked!" for n in notes)
    assert {n["badgeId"] for n in notes} == {"first_case", "clue_strategist"}

    # Soft uniqueness: second apply with same newly-unlocked set adds nothing.
    monkeypatch.setattr(
        "app.repositories.find_newly_unlocked",
        lambda **_kwargs: [first, strategist],
    )
    again = apply_badge_unlocks(store, user_id="u1", profile=profile)
    assert again == []
    assert len([n for n in store["notifications"] if n["userId"] == "u1"]) == 2
    assert len([b for b in store["user_badges"] if b["userId"] == "u1"]) == 2


def test_backfill_missing_badge_notifications_is_idempotent(monkeypatch):
    monkeypatch.setattr("app.repositories.get_challenges", lambda: [])
    store = {
        "user_badges": [
            {
                "id": "ub-1",
                "userId": "u1",
                "badgeId": "first_case",
                "earnedAt": "2026-01-01T00:00:00",
            }
        ],
        "notifications": [],
    }
    created = backfill_missing_badge_notifications(store, "u1", {"ageBand": "8_10"})
    assert created == 1
    assert len(store["notifications"]) == 1
    assert store["notifications"][0]["title"] == "New badge unlocked!"
    assert store["notifications"][0]["badgeId"] == "first_case"

    created_again = backfill_missing_badge_notifications(store, "u1", {"ageBand": "8_10"})
    assert created_again == 0
    assert len(store["notifications"]) == 1


def test_toast_message_contract_for_one_and_many_badges():
    """Document frontend toastMessageForBadges contract in backend-friendly form."""
    one = [
        {
            "title": "Clue Strategist",
            "reason": "You used clues successfully in three challenges.",
            "message": "You earned the Clue Strategist badge.",
        }
    ]
    multi = one + [{"title": "First Case", "reason": "You completed your first challenge."}]

    def toast_message_for_badges(badges):
        if not badges:
            return ""
        if len(badges) == 1:
            badge = badges[0]
            return "\n".join(
                line
                for line in [
                    "Badge unlocked!",
                    badge.get("title") or "New badge",
                    badge.get("reason") or badge.get("message") or "",
                ]
                if line
            )
        return f"You unlocked {len(badges)} new badges."

    assert toast_message_for_badges(one) == (
        "Badge unlocked!\n"
        "Clue Strategist\n"
        "You used clues successfully in three challenges."
    )
    assert toast_message_for_badges(multi) == "You unlocked 2 new badges."
