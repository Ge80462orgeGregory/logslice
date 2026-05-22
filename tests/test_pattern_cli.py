"""Integration tests for logslice.pattern_cli."""

import io
import json

import pytest

from logslice.pattern_cli import build_pattern_parser, run_pattern_cli


def _run(argv, lines):
    """Run the pattern CLI with *argv* and *lines* as stdin; return (rc, out, err)."""
    parser = build_pattern_parser()
    args = parser.parse_args(argv)
    in_stream = io.StringIO("\n".join(lines) + "\n")
    out_stream = io.StringIO()
    err_stream = io.StringIO()
    rc = run_pattern_cli(args, in_stream=in_stream, out_stream=out_stream, err_stream=err_stream)
    return rc, out_stream.getvalue(), err_stream.getvalue()


def _make_lines(records):
    return [json.dumps(r) for r in records]


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------

def test_no_patterns_returns_exit_2():
    rc, _, err = _run(["level"], _make_lines([{"level": "INFO"}]))
    assert rc == 2
    assert "error" in err


# ---------------------------------------------------------------------------
# Include filtering
# ---------------------------------------------------------------------------

def test_include_keeps_matching_records():
    lines = _make_lines([
        {"level": "ERROR", "msg": "boom"},
        {"level": "INFO", "msg": "ok"},
    ])
    rc, out, _ = _run(["level", "-i", "ERROR"], lines)
    assert rc == 0
    records = [json.loads(l) for l in out.strip().splitlines()]
    assert len(records) == 1
    assert records[0]["level"] == "ERROR"


# ---------------------------------------------------------------------------
# Exclude filtering
# ---------------------------------------------------------------------------

def test_exclude_removes_matching_records():
    lines = _make_lines([
        {"level": "DEBUG", "msg": "verbose"},
        {"level": "INFO", "msg": "ok"},
    ])
    rc, out, _ = _run(["level", "-e", "DEBUG"], lines)
    assert rc == 0
    records = [json.loads(l) for l in out.strip().splitlines()]
    assert len(records) == 1
    assert records[0]["level"] == "INFO"


# ---------------------------------------------------------------------------
# Case insensitivity flag
# ---------------------------------------------------------------------------

def test_ignore_case_flag():
    lines = _make_lines([{"level": "error"}, {"level": "INFO"}])
    rc, out, _ = _run(["level", "-i", "ERROR", "--ignore-case"], lines)
    assert rc == 0
    records = [json.loads(l) for l in out.strip().splitlines()]
    assert len(records) == 1
    assert records[0]["level"] == "error"


# ---------------------------------------------------------------------------
# Invalid JSON lines are skipped with a warning
# ---------------------------------------------------------------------------

def test_invalid_json_skipped():
    lines = ["not-json", json.dumps({"level": "ERROR", "msg": "ok"})]
    rc, out, err = _run(["level", "-i", "ERROR"], lines)
    assert rc == 0
    assert "skipping" in err
    records = [json.loads(l) for l in out.strip().splitlines()]
    assert len(records) == 1
