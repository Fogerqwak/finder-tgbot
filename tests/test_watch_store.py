from app.services.watch_store import WatchStore


def make_store(tmp_path) -> WatchStore:
    return WatchStore(str(tmp_path / "watch.db"))


def test_add_and_list(tmp_path):
    store = make_store(tmp_path)
    assert store.add(1, "alice") is True
    assert store.add(1, "bob") is True
    assert store.list_for_user(1) == ["alice", "bob"]
    assert store.count_for_user(1) == 2


def test_add_duplicate_case_insensitive_fails(tmp_path):
    store = make_store(tmp_path)
    assert store.add(1, "alice") is True
    assert store.add(1, "ALICE") is False
    assert store.count_for_user(1) == 1


def test_watch_lists_are_per_user(tmp_path):
    store = make_store(tmp_path)
    store.add(1, "alice")
    store.add(2, "alice")
    assert store.count_for_user(1) == 1
    assert store.count_for_user(2) == 1


def test_remove(tmp_path):
    store = make_store(tmp_path)
    store.add(1, "alice")
    assert store.remove(1, "ALICE") is True
    assert store.count_for_user(1) == 0
    assert store.remove(1, "alice") is False


def test_all_entries(tmp_path):
    store = make_store(tmp_path)
    store.add(1, "alice")
    store.add(2, "bob")
    entries = {(e.user_id, e.username) for e in store.all_entries()}
    assert entries == {(1, "alice"), (2, "bob")}


def test_remove_by_id(tmp_path):
    store = make_store(tmp_path)
    store.add(1, "alice")
    entry = store.all_entries()[0]
    store.remove_by_id(entry.id)
    assert store.all_entries() == []
