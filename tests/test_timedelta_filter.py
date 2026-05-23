"""Tests for logslice.timedelta_filter and logslice.timedelta_cli."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from io import StringIO

import pytest

from logslice.timedelta_filter import (
    TimedeltaFilter,
    TimedeltaFilterError,
    parse_duration,
)
from logslice.timedelta_cli import run_timedelta_cli


# ---------------------------------------------------------------------------
# parse_duration
# ---------------------------------------------------------------------------

def test_parse_duration_seconds():
    assert parse_duration("30s") == timedelta(seconds=30)


def test_parse_duration_minutes():
    assert parse_duration("5m") == timedelta(minutes=5)


def test_parse_duration_hours():
    assert parse_duration("2h") == timedelta(hours=2)


def test_parse_duration_days():
    assert parse_duration("1d") == timedelta(days=1)


def test_parse_duration_fractional():
    assert parse_duration("1.5h") == timedelta(hours=1.5)


def test_parse_duration_invalid_raises():
    with pytest.raises(TimedeltaFilterError, match="Cannot parse"):
        parse_duration("forever")


def test_parse_duration_unknown_unit_raises():
    with pytest.raises(TimedeltaFilterError, match="Unknown time unit"):
        parse_duration("5w")


# ---------------------------------------------------------------------------
# TimedeltaFilter construction
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(TimedeltaFilterError, match="field must not be empty"):
        TimedeltaFilter(window="5m", field="")


def test_field_property():
    tf = TimedeltaFilter(window="10s", field="ts")
    assert tf.field == "ts"


def test_window_property():
    tf = TimedeltaFilter(window="3h")
    assert tf.window == timedelta(hours=3)


# ---------------------------------------------------------------------------
# TimedeltaFilter.matches
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_matches_iso_within_window():
    tf = TimedeltaFilter(window="10m", now=_now())
    record = {"timestamp": "2024-06-01T11:55:00+00:00"}
    assert tf.matches(record) is True


def test_matches_iso_outside_window():
    tf = TimedeltaFilter(window="5m", now=_now())
    record = {"timestamp": "2024-06-01T11:50:00+00:00"}
    assert tf.matches(record) is False


def test_matches_unix_timestamp():
    now = _now()
    ts = now.timestamp() - 60  # 1 minute ago
    tf = TimedeltaFilter(window="5m", now=now)
    assert tf.matches({"timestamp": ts}) is True


def test_matches_missing_field_returns_false():
    tf = TimedeltaFilter(window="5m", now=_now())
    assert tf.matches({"level": "info"}) is False


def test_matches_unparseable_ts_returns_false():
    tf = TimedeltaFilter(window="5m", now=_now())
    assert tf.matches({"timestamp": "not-a-date"}) is False


def test_filter_records_yields_matching():
    now = _now()
    tf = TimedeltaFilter(window="10m", now=now)
    records = [
        {"timestamp": "2024-06-01T11:55:00+00:00", "msg": "ok"},
        {"timestamp": "2024-06-01T11:40:00+00:00", "msg": "old"},
    ]
    result = list(tf.filter_records(records))
    assert len(result) == 1
    assert result[0]["msg"] == "ok"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _run(argv, stdin_text=""):
    old_stdin = sys.stdin
    sys.stdin = StringIO(stdin_text)
    try:
        return run_timedelta_cli(argv)
    finally:
        sys.stdin = old_stdin


def test_cli_invalid_window_exits_2():
    code = _run(["forever"])
    assert code == 2


def test_cli_filters_within_window(capsys):
    now = datetime.now(tz=timezone.utc)
    recent = (now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    old = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    lines = (
        json.dumps({"timestamp": recent, "msg": "recent"}) + "\n"
        + json.dumps({"timestamp": old, "msg": "old"}) + "\n"
    )
    code = _run(["30m"], stdin_text=lines)
    captured = capsys.readouterr()
    assert code == 0
    assert "recent" in captured.out
    assert "old" not in captured.out


def test_cli_strict_exits_1_on_bad_json(capsys):
    code = _run(["5m", "--strict"], stdin_text="not json\n")
    assert code == 1
