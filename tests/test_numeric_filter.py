"""Tests for logslice.numeric_filter."""

import pytest

from logslice.numeric_filter import NumericFilter, NumericFilterError


def test_empty_field_raises():
    with pytest.raises(NumericFilterError, match="non-empty"):
        NumericFilter("", min_val=0)


def test_no_bounds_raises():
    with pytest.raises(NumericFilterError, match="at least one"):
        NumericFilter("latency")


def test_min_exceeds_max_raises():
    with pytest.raises(NumericFilterError, match="must not exceed"):
        NumericFilter("latency", min_val=100, max_val=50)


def test_field_property():
    f = NumericFilter("latency", min_val=0)
    assert f.field == "latency"


def test_min_val_property():
    f = NumericFilter("latency", min_val=5.5)
    assert f.min_val == 5.5


def test_max_val_property():
    f = NumericFilter("latency", max_val=99)
    assert f.max_val == 99


def test_matches_within_range():
    f = NumericFilter("latency", min_val=10, max_val=100)
    assert f.matches({"latency": 50}) is True


def test_matches_at_min_boundary():
    f = NumericFilter("latency", min_val=10, max_val=100)
    assert f.matches({"latency": 10}) is True


def test_matches_at_max_boundary():
    f = NumericFilter("latency", min_val=10, max_val=100)
    assert f.matches({"latency": 100}) is True


def test_matches_below_min_returns_false():
    f = NumericFilter("latency", min_val=10)
    assert f.matches({"latency": 9}) is False


def test_matches_above_max_returns_false():
    f = NumericFilter("latency", max_val=100)
    assert f.matches({"latency": 101}) is False


def test_matches_missing_field_returns_false():
    f = NumericFilter("latency", min_val=0)
    assert f.matches({"status": 200}) is False


def test_matches_non_numeric_field_returns_false():
    f = NumericFilter("latency", min_val=0)
    assert f.matches({"latency": "fast"}) is False


def test_matches_nested_field():
    f = NumericFilter("metrics.latency", min_val=1, max_val=50)
    assert f.matches({"metrics": {"latency": 25}}) is True


def test_matches_nested_field_out_of_range():
    f = NumericFilter("metrics.latency", min_val=1, max_val=50)
    assert f.matches({"metrics": {"latency": 99}}) is False


def test_matches_non_dict_raises():
    f = NumericFilter("latency", min_val=0)
    with pytest.raises(NumericFilterError, match="dict"):
        f.matches([1, 2, 3])  # type: ignore[arg-type]


def test_filter_many_returns_passing_records():
    f = NumericFilter("score", min_val=5, max_val=10)
    records = [{"score": 3}, {"score": 7}, {"score": 10}, {"score": 12}]
    result = f.filter_many(records)
    assert result == [{"score": 7}, {"score": 10}]


def test_filter_many_empty_list():
    f = NumericFilter("score", min_val=0)
    assert f.filter_many([]) == []


def test_only_max_bound_works():
    f = NumericFilter("size", max_val=1024)
    assert f.matches({"size": 512}) is True
    assert f.matches({"size": 2048}) is False
