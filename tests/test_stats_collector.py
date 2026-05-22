"""Tests for logslice.stats_collector."""

import pytest
from logslice.stats_collector import StatsCollector


def test_total_and_matched_counts() -> None:
    sc = StatsCollector()
    sc.record({"level": "info"}, matched=True)
    sc.record({"level": "debug"}, matched=False)
    sc.record({"level": "error"}, matched=True)

    assert sc.total == 3
    assert sc.matched == 2


def test_dropped_equals_total_minus_matched() -> None:
    sc = StatsCollector()
    for i in range(5):
        sc.record({}, matched=(i % 2 == 0))

    summary = sc.summary()
    assert summary["dropped"] == summary["total"] - summary["matched"]


def test_field_counts_single_field() -> None:
    sc = StatsCollector(count_fields=["level"])
    for level in ["info", "info", "error", "warn", "info"]:
        sc.record({"level": level}, matched=True)

    counts = sc.field_counts("level")
    assert counts["info"] == 3
    assert counts["error"] == 1
    assert counts["warn"] == 1


def test_field_counts_only_for_matched_records() -> None:
    sc = StatsCollector(count_fields=["level"])
    sc.record({"level": "info"}, matched=True)
    sc.record({"level": "debug"}, matched=False)  # should not be counted

    counts = sc.field_counts("level")
    assert counts.get("info") == 1
    assert "debug" not in counts


def test_missing_field_value_skipped() -> None:
    sc = StatsCollector(count_fields=["level"])
    sc.record({"msg": "no level here"}, matched=True)

    assert sc.field_counts("level") == {}


def test_summary_contains_field_counts_key() -> None:
    sc = StatsCollector(count_fields=["status"])
    sc.record({"status": "200"}, matched=True)
    sc.record({"status": "404"}, matched=True)

    summary = sc.summary()
    assert "counts:status" in summary
    assert summary["counts:status"]["200"] == 1
    assert summary["counts:status"]["404"] == 1


def test_reset_clears_all_state() -> None:
    sc = StatsCollector(count_fields=["level"])
    sc.record({"level": "info"}, matched=True)
    sc.reset()

    assert sc.total == 0
    assert sc.matched == 0
    assert sc.field_counts("level") == {}


def test_numeric_field_values_coerced_to_str() -> None:
    sc = StatsCollector(count_fields=["code"])
    sc.record({"code": 200}, matched=True)
    sc.record({"code": 200}, matched=True)

    counts = sc.field_counts("code")
    assert counts["200"] == 2


def test_field_counts_raises_for_untracked_field() -> None:
    """Requesting counts for a field not in count_fields should raise KeyError."""
    sc = StatsCollector(count_fields=["level"])
    sc.record({"level": "info", "status": "200"}, matched=True)

    with pytest.raises(KeyError):
        sc.field_counts("status")
