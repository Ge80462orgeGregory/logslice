"""Tests for logslice.aggregator."""

import pytest

from logslice.aggregator import Aggregator, AggregatorError


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_empty_fields_raises():
    with pytest.raises(AggregatorError, match="At least one field"):
        Aggregator(fields=[])


def test_single_field_initialises():
    agg = Aggregator(fields=["level"])
    assert agg.total == 0


# ---------------------------------------------------------------------------
# feed / feed_many
# ---------------------------------------------------------------------------

def test_feed_increments_total():
    agg = Aggregator(fields=["level"])
    agg.feed({"level": "info", "msg": "hello"})
    agg.feed({"level": "error", "msg": "boom"})
    assert agg.total == 2


def test_feed_non_dict_raises():
    agg = Aggregator(fields=["level"])
    with pytest.raises(AggregatorError, match="must be a dict"):
        agg.feed(["not", "a", "dict"])


def test_feed_many_counts_correctly():
    records = [
        {"level": "info"},
        {"level": "info"},
        {"level": "warn"},
    ]
    agg = Aggregator(fields=["level"])
    agg.feed_many(records)
    assert agg.counts("level")["info"] == 2
    assert agg.counts("level")["warn"] == 1


# ---------------------------------------------------------------------------
# counts / top
# ---------------------------------------------------------------------------

def test_counts_unknown_field_raises():
    agg = Aggregator(fields=["level"])
    with pytest.raises(AggregatorError, match="not tracked"):
        agg.counts("service")


def test_missing_field_value_skipped():
    agg = Aggregator(fields=["level"])
    agg.feed({"msg": "no level here"})
    assert agg.total == 1
    assert agg.counts("level") == {}


def test_top_returns_sorted_descending():
    records = [
        {"level": "info"},
        {"level": "info"},
        {"level": "info"},
        {"level": "warn"},
        {"level": "error"},
        {"level": "error"},
    ]
    agg = Aggregator(fields=["level"])
    agg.feed_many(records)
    top = agg.top("level")
    assert top[0] == ("info", 3)
    assert top[1][1] == 2  # error
    assert top[2][1] == 1  # warn


def test_top_n_limits_results():
    records = [{"svc": f"s{i}"} for i in range(20)]
    agg = Aggregator(fields=["svc"])
    agg.feed_many(records)
    assert len(agg.top("svc", n=5)) == 5


def test_top_unknown_field_raises():
    """top() should raise AggregatorError for fields not being tracked."""
    agg = Aggregator(fields=["level"])
    with pytest.raises(AggregatorError, match="not tracked"):
        agg.top("service")


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_contains_total_and_fields():
    agg = Aggregator(fields=["level", "service"])
    agg.feed({"level": "info", "service": "api"})
    s = agg.summary()
    assert s["total"] == 1
    assert "level" in s["fields"]
    assert "service" in s["fields"]


def test_summary_top_values_correct():
    agg =
