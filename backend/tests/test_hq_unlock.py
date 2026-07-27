from app import repositories as repo


def test_unlock_item_does_not_reduce_total_xp(temp_store):
    before = repo.get_profile_data("user-1")["profile"]["totalXp"]
    result = repo.purchase_hq_item("user-1", "chair-green")
    assert result["totalXp"] == before

    after = repo.get_profile_data("user-1")["profile"]["totalXp"]
    assert after == before
    assert "chair-green" in result["hqOwnedItemIds"]


def test_unlock_requires_enough_xp(temp_store):
    from app.storage import load_store, save_store

    store = load_store()
    profile = next(p for p in store["profiles"] if p["userId"] == "user-1")
    profile["totalXp"] = 50
    profile["currentLevelXp"] = 50
    save_store(store)

    try:
        repo.purchase_hq_item("user-1", "cabinet-green")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Not enough XP"


def test_unlock_duplicate_rejected(temp_store):
    repo.purchase_hq_item("user-1", "chair-brown")
    try:
        repo.purchase_hq_item("user-1", "chair-brown")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Already owned"
