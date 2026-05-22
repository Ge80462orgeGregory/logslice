"""Tests for logslice.dedup_filter."""

import pytest

from logslice.dedup_filter import DedupError, DedupFilter


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_invalid_window_raises():
    with pytest.raises(DedupError, match="window must be >= 1"):
        DedupFilter(window=0)


def test_default_window_is_1000():
    df = DedupFilter()
    assert df.window == 1000


# ---------------------------------------------------------------------------
# Basic dedup behaviour
# ---------------------------------------------------------------------------

def test_first_occurrence_not_duplicate():
    df = DedupFilter()
    assert df.is_duplicate({"level": "info", "msg": "hello"}) is False


def test_second_occurrence_is_duplicate():
    df = DedupFilter()
    record = {"level": "info", "msg": "hello"}
    df.is_duplicate(record)
    assert df.is_duplicate(record) is True


def test_different_records_not_duplicate():
    df = DedupFilter()
    df.is_duplicate({"msg": "a"})
    assert df.is_duplicate({"msg": "b"}) is False


# ---------------------------------------------------------------------------
# Field-scoped dedup
# ---------------------------------------------------------------------------

def test_field_scoped_dedup_ignores_other_fields():
    df = DedupFilter(fields=["msg"])
    df.is_duplicate({"msg": "same", "ts": "2024-01-01"})
    # Different ts but same msg — should be treated as duplicate
    assert df.is_duplicate({"msg": "same", "ts": "2024-01-02"}) is True


def test_field_scoped_dedup_nested_field():
    df = DedupFilter(fields=["error.code"])
    df.is_duplicate({"error": {"code": 404}})
    assert df.is_duplicate({"error": {"code": 404}}) is True
    assert df.is_duplicate({"error": {"code": 500}}) is False


def test_missing_nested_field_treated_as_none():
    df = DedupFilter(fields=["error.code"])
    df.is_duplicate({"msg": "no error field"})
    # Both records map to key=None for error.code → duplicate
    assert df.is_duplicate({"level": "warn"}) is True


# ---------------------------------------------------------------------------
# Window eviction
# ---------------------------------------------------------------------------

def test_window_evicts_oldest_key():
    df = DedupFilter(window=2)
    df.is_duplicate({"id": 1})
    df.is_duplicate({"id": 2})
    # Adding a third entry evicts {"id": 1}
    df.is_duplicate({"id": 3})
    # {"id": 1} should no longer be considered a duplicate
    assert df.is_duplicate({"id": 1}) is False


def test_seen_count_does_not_exceed_window():
    df = DedupFilter(window=5)
    for i in range(20):
        df.is_duplicate({"id": i})
    assert df.seen_count <= 5


# ---------------------------------------------------------------------------
# filter_records helper
# ---------------------------------------------------------------------------

def test_filter_records_removes_duplicates():
    df = DedupFilter(fields=["msg"])
    records = [
        {"msg": "a", "ts": 1},
        {"msg": "b", "ts": 2},
        {"msg": "a", "ts": 3},  # duplicate
        {"msg": "c", "ts": 4},
    ]
    result = list(df.filter_records(records))
    assert len(result) == 3
    assert result[0]["ts"] == 1
    assert result[1]["ts"] == 2
    assert result[2]["ts"] == 4


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

def test_reset_clears_seen_cache():
    df = DedupFilter()
    record = {"msg": "hello"}
    df.is_duplicate(record)
    df.reset()
    assert df.seen_count == 0
    assert df.is_duplicate(record) is False  # treated as fresh after reset
