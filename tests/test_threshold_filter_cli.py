"""Integration tests for the threshold filter CLI."""

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from logslice.threshold_filter_cli import run_threshold_cli


def _make_lines(*records: dict) -> str:
    return "\n".join(json.dumps(r) for r in records) + "\n"


def _run(argv: list[str], stdin: str) -> tuple[int, list[str]]:
    captured: list[str] = []
    with patch("sys.stdin", StringIO(stdin)), patch(
        "builtins.print", side_effect=lambda *a, **kw: captured.append(str(a[0]))
    ):
        code = run_threshold_cli(argv)
    return code, captured


def test_missing_field_exits_2():
    code, _ = _run(["--threshold", "10"], "")
    assert code == 2


def test_missing_threshold_exits_2():
    code, _ = _run(["--field", "v"], "")
    assert code == 2


def test_invalid_direction_exits_2():
    code, _ = _run(["--field", "v", "--threshold", "5", "--direction", "sideways"], "")
    assert code == 2


def test_above_keeps_high_values():
    lines = _make_lines({"v": 20}, {"v": 5}, {"v": 10})
    code, out = _run(["--field", "v", "--threshold", "10"], lines)
    assert code == 0
    values = [json.loads(l)["v"] for l in out]
    assert values == [20, 10]


def test_exclusive_drops_boundary():
    lines = _make_lines({"v": 10}, {"v": 11})
    code, out = _run(["--field", "v", "--threshold", "10", "--exclusive"], lines)
    assert code == 0
    values = [json.loads(l)["v"] for l in out]
    assert values == [11]


def test_below_keeps_low_values():
    lines = _make_lines({"v": 3}, {"v": 10}, {"v": 15})
    code, out = _run(["--field", "v", "--threshold", "10", "--direction", "below"], lines)
    assert code == 0
    values = [json.loads(l)["v"] for l in out]
    assert values == [3, 10]


def test_invert_flag_reverses_filter():
    lines = _make_lines({"v": 20}, {"v": 5})
    code, out = _run(["--field", "v", "--threshold", "10", "--invert"], lines)
    assert code == 0
    values = [json.loads(l)["v"] for l in out]
    assert values == [5]


def test_invalid_json_lines_skipped():
    stdin = "not-json\n" + json.dumps({"v": 15}) + "\n"
    code, out = _run(["--field", "v", "--threshold", "10"], stdin)
    assert code == 0
    assert len(out) == 1
