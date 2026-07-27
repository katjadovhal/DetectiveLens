"""Slot metadata used for responsive room editing."""

from app.hq_shop import HQ_SLOTS


def test_hq_slots_have_percentage_coordinates():
    for slot in HQ_SLOTS:
        assert 0 <= slot["x"] <= 100
        assert 0 <= slot["y"] <= 100
        assert isinstance(slot["zIndex"], int)


def test_hq_slots_cover_mvp_categories():
    categories = {slot["id"] for slot in HQ_SLOTS}
    assert categories == {"desk", "chair", "deskDecoration", "cabinet"}
