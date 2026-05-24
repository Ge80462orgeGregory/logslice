"""Tests for TruncateFilter and the truncate CLI."""

from __future__ import annotations

import json
import pytest

from logslice.truncate_filter import TruncateFilter, TruncateFilterError
from logslice.truncate_cli import build_truncate_parser, run_truncate_cli


# ---------------------------------------------------------------------------
# TruncateFilter unit tests
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(TruncateFilterError):
        TruncateFilter(field="", max_length=10)


def test_blank_field_raises():
    with pytest.raises(TruncateFilterError):
        TruncateFilter(field="   ", max_length=10)


def test_zero_max_length_raises():
    with pytest.raises(TruncateFilterError):
        TruncateFilter(field="msg", max_length=0)


def test_negative_max_length_raises():
    with pytest.raises(TruncateFilterError):
        TruncateFilter(field="msg", max_length=-5)


def test_field_property():
    tf = TruncateFilter(field="message", max_length=20)
    assert tf.field == "message"


def test_max_length_property():
    tf = TruncateFilter(field="msg", max_length=15)
    assert tf.max_length == 15


def test_suffix_property():
    tf = TruncateFilter(field="msg", max_length=5, suffix="...")
    assert tf.suffix == "..."


def test_short_value_unchanged():
    tf = TruncateFilter(field="msg", max_length=100)
    record = {"msg": "hello"}
    result = tf.apply(record)
    assert result == {"msg": "hello"}


def test_long_value_truncated():
    tf = TruncateFilter(field="msg", max_length=5)
    result = tf.apply({"msg": "hello world"})
    assert result == {"msg": "hello"}


def test_truncation_with_suffix():
    tf = TruncateFilter(field="msg", max_length=5, suffix="...")
    result = tf.apply({"msg": "hello world"})
    assert result == {"msg": "hello..."}


def test_exact_length_not_truncated():
    tf = TruncateFilter(field="msg", max_length=5)
    result = tf.apply({"msg": "hello"})
    assert result == {"msg": "hello"}


def test_non_string_field_passed_through():
    tf = TruncateFilter(field="count", max_length=5)
    record = {"count": 42}
    result = tf.apply(record)
    assert result == {"count": 42}


def test_non_string_field_dropped_when_flag_set():
    tf = TruncateFilter(field="count", max_length=5, drop_non_string=True)
    result = tf.apply({"count": 42})
    assert result is None


def test_missing_field_passed_through():
    tf = TruncateFilter(field="missing", max_length=5)
    record = {"other": "value"}
    result = tf.apply(record)
    assert result == {"other": "value"}


def test_nested_field_truncated():
    tf = TruncateFilter(field="meta.description", max_length=4)
    record = {"meta": {"description": "long description here"}}
    result = tf.apply(record)
    assert result["meta"]["description"] == "long"


def test_apply_does_not_mutate_original():
    tf = TruncateFilter(field="msg", max_length=3)
    original = {"msg": "hello"}
    tf.apply(original)
    assert original["msg"] == "hello"


def test_non_dict_record_raises():
    tf = TruncateFilter(field="msg", max_length=5)
    with pytest.raises(TruncateFilterError):
        tf.apply(["not", "a", "dict"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _make_lines(*records):
    return [json.dumps(r) for r in records]


def _run(argv, lines):
    parser = build_truncate_parser()
    args = parser.parse_args(argv)
    from io import StringIO
    buf = StringIO()
    rc = run_truncate_cli(args, lines, out=buf)
    return rc, buf.getvalue().strip().splitlines()


def test_missing_field_exits_2():
    parser = build_truncate_parser()
    args = parser.parse_args(["--field", "", "--max-length", "10"])
    from io import StringIO
    rc = run_truncate_cli(args, [], out=StringIO())
    assert rc == 2


def test_cli_truncates_field():
    lines = _make_lines({"msg": "hello world", "level": "info"})
    rc, out = _run(["--field", "msg", "--max-length", "5"], lines)
    assert rc == 0
    assert json.loads(out[0])["msg"] == "hello"


def test_cli_suffix_appended():
    lines = _make_lines({"msg": "hello world"})
    rc, out = _run(["--field", "msg", "--max-length", "5", "--suffix", "…"], lines)
    assert rc == 0
    assert json.loads(out[0])["msg"] == "hello…"


def test_cli_invalid_json_passed_through():
    lines = ["not json\n"]
    rc, out = _run(["--field", "msg", "--max-length", "5"], lines)
    assert rc == 0
    assert out[0] == "not json"
