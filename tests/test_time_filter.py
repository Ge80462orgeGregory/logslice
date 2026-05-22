"""Tests for logslice.time_filter."""

import datetime
import pytest

from logslice.time_filter import TimeFilter, TimeFilterError, _parse_dt


# ---------------------------------------------------------------------------
# _parse_dt helpers
# ---------------------------------------------------------------------------

def test_parse_dt_iso_with_t():
    dt = _parse_dt("2024-03-15T12:30:00")
    assert dt == datetime.datetime(2024, 3, 15, 12, 30, 0)


def test_parse_dt_space_separator():
    dt = _parse_dt("2024-03-15 12:30:00")
    assert dt == datetime.datetime(2024, 3, 15, 12, 30, 0)


def test_parse_dt_date_only():
    dt = _parse_dt("2024-03-15")
    assert dt == datetime.datetime(2024, 3, 15, 0, 0, 0)


def test_parse_dt_invalid_raises():
    with pytest.raises(TimeFilterError, match="Cannot parse timestamp"):
        _parse_dt("not-a-date")


# ---------------------------------------------------------------------------
# TimeFilter construction
# ---------------------------------------------------------------------------

def test_no_bounds_raises():
    with pytest.raises(TimeFilterError, match="At least one"):
        TimeFilter(since=None, until=None)


def test_empty_field_raises():
    with pytest.raises(TimeFilterError, match="field must not be empty"):
        TimeFilter(field="", since="2024-01-01")


def test_since_after_until_raises():
    with pytest.raises(TimeFilterError, match="must not be later"):
        TimeFilter(since="2024-06-01", until="2024-01-01")


# ---------------------------------------------------------------------------
# TimeFilter.matches
# ---------------------------------------------------------------------------

def _make_record(ts: str, field: str = "timestamp") -> dict:
    return {field: ts}


def test_matches_within_range():
    tf = TimeFilter(since="2024-01-01T00:00:00", until="2024-12-31T23:59:59")
    assert tf.matches(_make_record("2024-06-15T10:00:00")) is True


def test_matches_before_since_returns_false():
    tf = TimeFilter(since="2024-06-01T00:00:00", until="2024-12-31T23:59:59")
    assert tf.matches(_make_record("2024-01-01T00:00:00")) is False


def test_matches_after_until_returns_false():
    tf = TimeFilter(since="2024-01-01", until="2024-06-01")
    assert tf.matches(_make_record("2024-12-01T00:00:00")) is False


def test_matches_on_boundary_inclusive():
    tf = TimeFilter(since="2024-06-01T00:00:00", until="2024-06-01T00:00:00")
    assert tf.matches(_make_record("2024-06-01T00:00:00")) is True


def test_matches_only_since_no_upper_bound():
    tf = TimeFilter(since="2024-06-01")
    assert tf.matches(_make_record("2025-01-01T00:00:00")) is True
    assert tf.matches(_make_record("2023-01-01T00:00:00")) is False


def test_matches_only_until_no_lower_bound():
    tf = TimeFilter(until="2024-06-01")
    assert tf.matches(_make_record("2023-01-01T00:00:00")) is True
    assert tf.matches(_make_record("2025-01-01T00:00:00")) is False


def test_missing_field_returns_false():
    tf = TimeFilter(since="2024-01-01")
    assert tf.matches({"other_field": "2024-06-01T00:00:00"}) is False


def test_matches_custom_field():
    """TimeFilter should read timestamps from a user-specified field name."""
    tf = TimeFilter(field="logged_at", since="2024-01-01", until="2024-12-31")
    assert tf.matches(_make_record("2024-06-15T10:00:00", field="logged_at")) is True
    assert tf.matches(_make_record("2023-12-31T23:59:59", field="logged_at")) is False
