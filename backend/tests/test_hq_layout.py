from app import repositories as repo
from app.hq_shop import DEFAULT_HQ_LAYOUT, normalize_hq_layout


def test_legacy_profile_without_hq_layout_gets_default(temp_store):
    data = repo.get_profile_data("user-1")
    layout = data["profile"]["hqLayout"]
    assert layout == normalize_hq_layout(None)
    assert layout["desk"] == DEFAULT_HQ_LAYOUT["desk"]


def test_save_owned_layout_persists(temp_store):
    layout = {
        "desk": "desk-dark",
        "chair": None,
        "deskDecoration": None,
        "cabinet": None,
    }
    result = repo.update_profile("user-1", {"hqLayout": layout})
    assert result["profile"]["hqLayout"]["desk"] == "desk-dark"

    reloaded = repo.get_profile_data("user-1")
    assert reloaded["profile"]["hqLayout"]["desk"] == "desk-dark"


def test_save_unowned_item_rejected(temp_store):
    layout = {
        "desk": "desk-dark",
        "chair": "chair-green",
        "deskDecoration": None,
        "cabinet": None,
    }
    try:
        repo.update_profile("user-1", {"hqLayout": layout})
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Item not owned"


def test_save_wrong_category_rejected(temp_store):
    layout = {
        "desk": "chair-brown",
        "chair": None,
        "deskDecoration": None,
        "cabinet": None,
    }
    try:
        repo.update_profile("user-1", {"hqLayout": layout})
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "slot" in str(exc).lower()


def test_unknown_item_id_sanitized_to_null(temp_store):
    layout = {
        "desk": "unknown-item",
        "chair": None,
        "deskDecoration": None,
        "cabinet": None,
    }
    result = repo.update_profile("user-1", {"hqLayout": layout})
    assert result["profile"]["hqLayout"]["desk"] is None
