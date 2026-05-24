"""Tests for logslice.sequence_filter_cli."""
import json
from types import SimpleNamespace

import pytest

from logslice.sequence_filter_cli import build_sequence_filter_parser, run_sequence_filter_cli


def _make_lines(records):
    return [json.dumps(r) for r in records]


def _run(argv, lines):
    parser = build_sequence_filter_parser()
    args = parser.parse_args(argv)
    output = []
    code = run_sequence_filter_cli(args, lines, print_fn=output.append)
    return code, output


def test_missing_field_exits_2():
    code, _ = _run(["--field", "  "], _make_lines([{"n": 1}]))
    assert code == 2


def test_increasing_keeps_correct_records():
    records = [{"n": 1}, {"n": 3}, {"n": 2}, {"n": 5}]
    code, out = _run(["--field", "n"], _make_lines(records))
    assert code == 0
    parsed = [json.loads(l) for l in out]
    assert [r["n"] for r in parsed] == [1, 3, 5]


def test_decreasing_flag_keeps_correct_records():
    records = [{"n": 10}, {"n": 8}, {"n": 9}, {"n": 3}]
    code, out = _run(["--field", "n", "--decreasing"], _make_lines(records))
    assert code == 0
    parsed = [json.loads(l) for l in out]
    assert [r["n"] for r in parsed] == [10, 8, 3]


def test_invalid_json_lines_skipped():
    lines = ["not json", json.dumps({"n": 1}), "also bad", json.dumps({"n": 2})]
    code, out = _run(["--field", "n"], lines)
    assert code == 0
    assert len(out) == 2


def test_empty_lines_skipped():
    lines = ["", "   ", json.dumps({"n": 1})]
    code, out = _run(["--field", "n"], lines)
    assert code == 0
    assert len(out) == 1


def test_nested_field_cli():
    records = [{"a": {"b": 1}}, {"a": {"b": 2}}, {"a": {"b": 1}}]
    code, out = _run(["--field", "a.b"], _make_lines(records))
    assert code == 0
    parsed = [json.loads(l) for l in out]
    assert len(parsed) == 2
    assert parsed[0]["a"]["b"] == 1
    assert parsed[1]["a"]["b"] == 2
