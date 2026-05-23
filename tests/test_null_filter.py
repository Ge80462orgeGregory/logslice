"""Tests for logslice.null_filter."""

import pytest

from logslice.null_filter import NullFilter, NullFilterError


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(NullFilterError):
        NullFilter("")


def test_blank_field_raises():
    with pytest.raises(NullFilterError):
        NullFilter("   ")


def test_valid_construction():
    f = NullFilter("status")
    assert f.field == "status"
    assert f.drop_null is True


def test_invert_construction():
    f = NullFilter("status", drop_null=False)
    assert f.drop_null is False


# ---------------------------------------------------------------------------
# keep() — drop_null=True (default)
# ---------------------------------------------------------------------------

def test_keep_present_non_null():
    f = NullFilter("status")
    assert f.keep({"status": "ok"}) is True


def test_drop_explicit_null():
    f = NullFilter("status")
    assert f.keep({"status": None}) is False


def test_drop_missing_field():
    f = NullFilter("status")
    assert f.keep({"level": "info"}) is False


def test_keep_zero_value_not_null():
    """Zero is falsy but not None — should be kept."""
    f = NullFilter("count")
    assert f.keep({"count": 0}) is True


def test_keep_empty_string_not_null():
    f = NullFilter("msg")
    assert f.keep({"msg": ""}) is True


# ---------------------------------------------------------------------------
# keep() — drop_null=False (keep only null/missing)
# ---------------------------------------------------------------------------

def test_invert_keeps_null():
    f = NullFilter("status", drop_null=False)
    assert f.keep({"status": None}) is True


def test_invert_keeps_missing():
    f = NullFilter("status", drop_null=False)
    assert f.keep({"level": "info"}) is True


def test_invert_drops_present_non_null():
    f = NullFilter("status", drop_null=False)
    assert f.keep({"status": "ok"}) is False


# ---------------------------------------------------------------------------
# Nested fields
# ---------------------------------------------------------------------------

def test_nested_field_present():
    f = NullFilter("http.status")
    assert f.keep({"http": {"status": 200}}) is True


def test_nested_field_null():
    f = NullFilter("http.status")
    assert f.keep({"http": {"status": None}}) is False


def test_nested_field_missing_parent():
    f = NullFilter("http.status")
    assert f.keep({"level": "warn"}) is False


# ---------------------------------------------------------------------------
# filter() iterable helper
# ---------------------------------------------------------------------------

def test_filter_removes_nulls():
    f = NullFilter("x")
    records = [{"x": 1}, {"x": None}, {"y": 2}, {"x": 3}]
    result = list(f.filter(records))
    assert result == [{"x": 1}, {"x": 3}]


def test_filter_invert_keeps_only_nulls():
    f = NullFilter("x", drop_null=False)
    records = [{"x": 1}, {"x": None}, {"y": 2}]
    result = list(f.filter(records))
    assert result == [{"x": None}, {"y": 2}]


# ---------------------------------------------------------------------------
# Error on non-dict record
# ---------------------------------------------------------------------------

def test_keep_non_dict_raises():
    f = NullFilter("field")
    with pytest.raises(NullFilterError):
        f.keep("not a dict")
