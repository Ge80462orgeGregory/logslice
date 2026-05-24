"""Tests for logslice.count_filter_cli."""
from __future__ import annotations

import io
import json
from typing import List

from logslice.count_filter_cli import run_count_filter_cli


def _make_lines(records: List[dict]) -> io.StringIO:
    return io.StringIO("\n".join(json.dumps(r) for r in records) + "\n")


def _run(argv, records):
    stdin = _make_lines(records)
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run_count_filter_cli(argv, stdin=stdin, stdout=stdout, stderr=stderr)
    out_lines = [json.loads(l) for l in stdout.getvalue().splitlines() if l.strip()]
    return code, out_lines, stderr.getvalue()


def test_missing_field_exits_2():
    stdin = io.StringIO()
    stderr = io.StringIO()
    code = run_count_filter_cli(["--min", "1"], stdin=stdin, stdout=io.StringIO(), stderr=stderr)
    assert code == 2


def test_no_bounds_exits_2():
    stdin = io.StringIO()
    stderr = io.StringIO()
    code = run_count_filter_cli(["--field", "level"], stdin=stdin, stdout=io.StringIO(), stderr=stderr)
    assert code == 2
    assert "error" in stderr.getvalue()


def test_min_count_filters_first_occurrence():
    records = [{"level": "error"}, {"level": "error"}, {"level": "error"}]
    code, out, _ = _run(["--field", "level", "--min", "2"], records)
    assert code == 0
    assert len(out) == 2


def test_max_count_drops_after_threshold():
    records = [{"level": "warn"}] * 4
    code, out, _ = _run(["--field", "level", "--max", "2"], records)
    assert code == 0
    assert len(out) == 2


def test_invert_flag():
    records = [{"level": "info"}] * 3
    code, out, _ = _run(["--field", "level", "--max", "1", "--invert"], records)
    assert code == 0
    # first occurrence is in range → inverted → dropped; remaining 2 pass
    assert len(out) == 2


def test_invalid_json_skipped():
    stdin = io.StringIO('{"level": "ok"}\nnot-json\n{"level": "ok"}\n')
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run_count_filter_cli(["--field", "level", "--min", "1"], stdin=stdin, stdout=stdout, stderr=stderr)
    assert code == 0
    assert "warning" in stderr.getvalue()
    lines = [l for l in stdout.getvalue().splitlines() if l.strip()]
    assert len(lines) == 2
