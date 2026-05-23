"""Tests for logslice.percentile."""

import pytest
from logslice.percentile import Percentile, PercentileError


def test_empty_field_raises():
    with pytest.raises(PercentileError, match="non-empty"):
        Percentile("")


def test_out_of_range_percentile_raises():
    with pytest.raises(PercentileError, match="out of range"):
        Percentile("latency", percentiles=[50.0, 101.0])


def test_negative_percentile_raises():
    with pytest.raises(PercentileError, match="out of range"):
        Percentile("latency", percentiles=[-1.0])


def test_field_property():
    p = Percentile("duration")
    assert p.field == "duration"


def test_requested_defaults():
    p = Percentile("x")
    assert p.requested == [50.0, 90.0, 95.0, 99.0]


def test_feed_non_dict_raises():
    p = Percentile("x")
    with pytest.raises(PercentileError, match="dict"):
        p.feed([1, 2, 3])  # type: ignore[arg-type]


def test_missing_field_increments_skipped():
    p = Percentile("latency")
    p.feed({"other": 1})
    assert p.count == 0
    assert p.skipped == 1


def test_non_numeric_value_increments_skipped():
    p = Percentile("latency")
    p.feed({"latency": "fast"})
    assert p.count == 0
    assert p.skipped == 1


def test_valid_feed_increments_count():
    p = Percentile("latency")
    p.feed({"latency": 42})
    assert p.count == 1
    assert p.skipped == 0


def test_feed_many_counts_correctly():
    p = Percentile("v")
    records = [{"v": i} for i in range(10)]
    p.feed_many(records)
    assert p.count == 10


def test_compute_raises_with_no_data():
    p = Percentile("v")
    with pytest.raises(PercentileError, match="no numeric values"):
        p.compute()


def test_compute_single_value():
    p = Percentile("v", percentiles=[50.0, 99.0])
    p.feed({"v": 7.0})
    result = p.compute()
    assert result[50.0] == 7.0
    assert result[99.0] == 7.0


def test_compute_p50_of_sorted_list():
    p = Percentile("v", percentiles=[50.0])
    for val in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        p.feed({"v": val})
    result = p.compute()
    # median of 1-10 should be between 5 and 6
    assert 5.0 <= result[50.0] <= 6.0


def test_compute_p0_and_p100():
    p = Percentile("v", percentiles=[0.0, 100.0])
    p.feed_many([{"v": v} for v in [3, 1, 4, 1, 5, 9, 2, 6]])
    result = p.compute()
    assert result[0.0] == 1.0
    assert result[100.0] == 9.0


def test_summary_returns_sorted_tuples():
    p = Percentile("v", percentiles=[99.0, 50.0, 90.0])
    p.feed_many([{"v": i} for i in range(100)])
    summary = p.summary()
    keys = [k for k, _ in summary]
    assert keys == sorted(keys)


def test_string_numeric_value_accepted():
    p = Percentile("v", percentiles=[50.0])
    p.feed({"v": "123.4"})
    assert p.count == 1
    result = p.compute()
    assert result[50.0] == pytest.approx(123.4)
