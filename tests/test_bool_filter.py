"""Tests for logslice.bool_filter."""

import pytest

from logslice.bool_filter import BoolFilter, BoolFilterError


# ---------------------------------------------------------------------------
# Construction errors
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(BoolFilterError, match="empty"):
        BoolFilter("")


def test_blank_field_raises():
    with pytest.raises(BoolFilterError, match="empty"):
        BoolFilter("   ")


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_field_property():
    f = BoolFilter("active")
    assert f.field == "active"


def test_expected_defaults_to_true():
    f = BoolFilter("active")
    assert f.expected is True


def test_expected_false_stored_correctly():
    f = BoolFilter("active", expected=False)
    assert f.expected is False


def test_invert_flips_expected():
    f = BoolFilter("active", expected=True, invert=True)
    assert f.expected is False


def test_strict_default_false():
    f = BoolFilter("active")
    assert f.strict is False


# ---------------------------------------------------------------------------
# matches — basic cases
# ---------------------------------------------------------------------------

def test_true_field_kept_when_expected_true():
    f = BoolFilter("active")
    assert f.matches({"active": True}) is True


def test_false_field_dropped_when_expected_true():
    f = BoolFilter("active")
    assert f.matches({"active": False}) is False


def test_false_field_kept_when_expected_false():
    f = BoolFilter("active", expected=False)
    assert f.matches({"active": False}) is True


def test_missing_field_passes_through_non_strict():
    f = BoolFilter("active", strict=False)
    assert f.matches({"other": 1}) is True


def test_missing_field_rejected_in_strict_mode():
    f = BoolFilter("active", strict=True)
    assert f.matches({"other": 1}) is False


def test_non_bool_value_passes_non_strict():
    f = BoolFilter("active", strict=False)
    assert f.matches({"active": 1}) is True


def test_non_bool_value_rejected_strict():
    f = BoolFilter("active", strict=True)
    assert f.matches({"active": 1}) is False


# ---------------------------------------------------------------------------
# Nested field support
# ---------------------------------------------------------------------------

def test_nested_field_matched():
    f = BoolFilter("user.verified")
    assert f.matches({"user": {"verified": True}}) is True


def test_nested_field_false_dropped():
    f = BoolFilter("user.verified")
    assert f.matches({"user": {"verified": False}}) is False


def test_deeply_nested_missing_non_strict():
    f = BoolFilter("a.b.c", strict=False)
    assert f.matches({"a": {}}) is True


# ---------------------------------------------------------------------------
# filter helper
# ---------------------------------------------------------------------------

def test_filter_returns_only_matching():
    f = BoolFilter("enabled")
    records = [
        {"enabled": True, "id": 1},
        {"enabled": False, "id": 2},
        {"enabled": True, "id": 3},
    ]
    result = f.filter(records)
    assert [r["id"] for r in result] == [1, 3]


def test_non_dict_record_raises():
    f = BoolFilter("active")
    with pytest.raises(BoolFilterError, match="dict"):
        f.matches(["not", "a", "dict"])  # type: ignore[arg-type]
