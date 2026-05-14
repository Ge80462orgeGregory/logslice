"""Tests for logslice.bookmark."""

import json
import os
import pytest

from logslice.bookmark import Bookmark, BookmarkError


@pytest.fixture()
def store(tmp_path):
    return Bookmark(str(tmp_path / "bookmarks.json"))


def test_get_returns_none_for_unknown_file(store, tmp_path):
    assert store.get(str(tmp_path / "app.log")) is None


def test_set_and_get_roundtrip(store, tmp_path):
    log = str(tmp_path / "app.log")
    store.set(log, 1024)
    assert store.get(log) == 1024


def test_set_persists_to_disk(tmp_path):
    log = str(tmp_path / "app.log")
    store_path = str(tmp_path / "bookmarks.json")
    b1 = Bookmark(store_path)
    b1.set(log, 512)
    b2 = Bookmark(store_path)
    assert b2.get(log) == 512


def test_set_negative_offset_raises(store, tmp_path):
    with pytest.raises(BookmarkError, match="non-negative"):
        store.set(str(tmp_path / "app.log"), -1)


def test_clear_removes_existing_bookmark(store, tmp_path):
    log = str(tmp_path / "app.log")
    store.set(log, 256)
    removed = store.clear(log)
    assert removed is True
    assert store.get(log) is None


def test_clear_returns_false_for_unknown_file(store, tmp_path):
    assert store.clear(str(tmp_path / "missing.log")) is False


def test_all_returns_copy(store, tmp_path):
    log = str(tmp_path / "app.log")
    store.set(log, 100)
    snapshot = store.all()
    snapshot["extra"] = 99
    assert "extra" not in store.all()


def test_load_corrupt_file_raises(tmp_path):
    store_path = tmp_path / "bookmarks.json"
    store_path.write_text("not-json")
    with pytest.raises(BookmarkError, match="Failed to load"):
        Bookmark(str(store_path))


def test_uses_absolute_path_as_key(store, tmp_path):
    log = str(tmp_path / "app.log")
    store.set(log, 42)
    keys = list(store.all().keys())
    assert keys[0] == os.path.abspath(log)
