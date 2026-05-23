"""Tests for logslice.burst_cli."""

from __future__ import annotations

import io
import json

import pytest

from logslice.burst_cli import build_burst_parser, run_burst_cli


def _run(argv: list[str], lines: list[str]):
    parser = build_burst_parser()
    args = parser.parse_args(argv)
    out = io.StringIO()
    err = io.StringIO()
    code = run_burst_cli(args, iter(lines), out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def _make_lines(n: int) -> list[str]:
    return [json.dumps({"msg": f"line {i}"}) for i in range(n)]


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_invalid_threshold_exits_2():
    code, _, err = _run(["--threshold", "0", "--window", "1"], _make_lines(1))
    assert code == 2
    assert "error" in err.lower()


def test_invalid_window_exits_2():
    code, _, err = _run(["--threshold", "3", "--window", "-1"], _make_lines(1))
    assert code == 2


# ---------------------------------------------------------------------------
# Normal operation — no passthrough
# ---------------------------------------------------------------------------

def test_no_burst_produces_no_output():
    lines = _make_lines(2)
    code, out, _ = _run(["--threshold", "5", "--window", "60"], lines)
    assert code == 0
    assert out == ""


def test_burst_warning_emitted():
    # threshold=2, so 3rd event triggers a burst
    lines = _make_lines(3)
    code, out, _ = _run(["--threshold", "2", "--window", "60"], lines)
    assert code == 0
    output_lines = [l for l in out.strip().splitlines() if l]
    assert len(output_lines) >= 1
    record = json.loads(output_lines[0])
    assert record["_burst_warning"] is True
    assert record["threshold"] == 2


def test_custom_warn_field():
    lines = _make_lines(4)
    code, out, _ = _run(
        ["--threshold", "1", "--window", "60", "--warn-field", "ALERT"],
        lines,
    )
    assert code == 0
    for raw in out.strip().splitlines():
        record = json.loads(raw)
        assert "ALERT" in record


# ---------------------------------------------------------------------------
# Passthrough mode
# ---------------------------------------------------------------------------

def test_passthrough_emits_all_input_lines():
    lines = _make_lines(3)
    code, out, _ = _run(
        ["--threshold", "10", "--window", "60", "--passthrough"],
        lines,
    )
    assert code == 0
    output_lines = out.strip().splitlines()
    # All 3 input lines should appear
    assert len(output_lines) == 3


def test_passthrough_plus_burst_warning():
    lines = _make_lines(3)
    code, out, _ = _run(
        ["--threshold", "2", "--window", "60", "--passthrough"],
        lines,
    )
    assert code == 0
    output_lines = out.strip().splitlines()
    # 3 input lines + 1 burst warning
    assert len(output_lines) == 4
