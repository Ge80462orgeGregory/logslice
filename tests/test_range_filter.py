"""Tests for logslice.range_filter."""

import pytest

from logslice.range_filter import RangeFilter, RangeFilterError


def test_empty_field_raises():
    with pytest.raises(RangeFilterError, match="field"):
        RangeFilter("", ["a", "b"])


def test_blank_field_raises():
    with pytest.raises(RangeFilterError, match="field"):
        RangeFilter("   ", ["a"])


def test_no_values_raises():
    with pytest.raises(RangeFilterError, match="at least one value"):
        RangeFilter("status", [])


def test_field_property():
    rf = RangeFilter("level", ["info", "warn"])
    assert rf.field == "level"


def test_values_property():
    rf = RangeFilter("level", ["info", "warn"])
    assert rf.values == {"info", "warn"}


def test_invert_defaults_false():
    rf = RangeFilter("level", ["info"])
    assert rf.invert is False


def test_case_sensitive_defaults_true():
    rf = RangeFilter("level", ["info"])
    assert rf.case_sensitive is True


def test_matching_record_kept():
    rf = RangeFilter("level", ["info", "warn"])
    assert rf.matches({"level": "info"}) is True


def test_non_matching_record_dropped():
    rf = RangeFilter("level", ["info", "warn"])
    assert rf.matches({"level": "error"}) is False


def test_invert_keeps_non_matching():
    rf = RangeFilter("level", ["info", "warn"], invert=True)
    assert rf.matches({"level": "error"}) is True


def test_invert_drops_matching():
    rf = RangeFilter("level", ["info", "warn"], invert=True)
    assert rf.matches({"level": "info"}) is False


def test_case_insensitive_match():
    rf = RangeFilter("level", ["info", "warn"], case_sensitive=False)
    assert rf.matches({"level": "INFO"}) is True


def test_case_sensitive_no_match():
    rf = RangeFilter("level", ["info"], case_sensitive=True)
    assert rf.matches({"level": "INFO"}) is False


def test_missing_field_returns_false():
    rf = RangeFilter("level", ["info"])
    assert rf.matches({"message": "hello"}) is False


def test_nested_field_match():
    rf = RangeFilter("http.method", ["GET", "POST"])
    assert rf.matches({"http": {"method": "GET"}}) is True


def test_nested_field_no_match():
    rf = RangeFilter("http.method", ["GET", "POST"])
    assert rf.matches({"http": {"method": "DELETE"}}) is False


def test_numeric_values():
    rf = RangeFilter("status", [200, 201, 204])
    assert rf.matches({"status": 200}) is True
    assert rf.matches({"status": 404}) is False


def test_non_dict_record_raises():
    rf = RangeFilter("level", ["info"])
    with pytest.raises(RangeFilterError, match="dict"):
        rf.matches(["not", "a", "dict"])


def test_filter_yields_matching_records():
    rf = RangeFilter("env", ["prod", "staging"])
    records = [
        {"env": "prod", "msg": "a"},
        {"env": "dev", "msg": "b"},
        {"env": "staging", "msg": "c"},
        {"env": "test", "msg": "d"},
    ]
    result = list(rf.filter(records))
    assert len(result) == 2
    assert result[0]["msg"] == "a"
    assert result[1]["msg"] == "c"


def test_filter_invert_yields_excluded_records():
    rf = RangeFilter("env", ["prod"], invert=True)
    records = [{"env": "prod"}, {"env": "dev"}, {"env": "staging"}]
    result = list(rf.filter(records))
    assert all(r["env"] != "prod" for r in result)
    assert len(result) == 2
