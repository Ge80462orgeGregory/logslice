"""Integration tests for the histogram CLI."""

from __future__ import annotations

import json
from io import StringIO
from typing import List
from unittest.mock import patch

import pytest

from logslice.histogram_cli import run_histogram_cli


def _make_lines(records: List[dict]) -> str:
    return "\n".join(json.dumps(r) for r in records) + "\n"


def _run(argv: List[str], stdin_text: str = "") -> tuple[int, str]:
    """Run the CLI and capture stdout."""
    import io
    import sys

    captured = io.StringIO()
    stdin = StringIO(stdin_text)
    with patch("sys.stdin", stdin), patch("sys.stdout", captured):
        code = run_histogram_cli(argv)
    return code, captured.getvalue()


def test_no_field_exits_nonzero():
    """Missing positional arg should cause argparse to exit 2."""
    with pytest.raises(SystemExit) as exc_info:
        run_histogram_cli([])
    assert exc_info.value.code == 2


def test_invalid_bucket_size_exits_2():
    code, _ = _run(["latency", "--bucket-size", "-1"])
    assert code == 2


def test_basic_output_contains_hash():
    lines = _make_lines([{"latency": i * 10} for i in range(5)])
    code, out = _run(["latency", "--bucket-size", "10"], stdin_text=lines)
    assert code == 0
    assert "#" in out


def test_total_line_in_output():
    lines = _make_lines([{"v": 1}, {"v": 2}, {"v": 3}])
    code, out = _run(["v", "--bucket-size", "1"], stdin_text=lines)
    assert code == 0
    assert "total: 3" in out


def test_skipped_reported_for_missing_field():
    lines = _make_lines([{"v": 1}, {"other": 99}])
    code, out = _run(["v", "--bucket-size", "1"], stdin_text=lines)
    assert code == 0
    assert "skipped: 1" in out


def test_no_data_shows_no_data():
    code, out = _run(["v", "--bucket-size", "1"], stdin_text="")
    assert code == 0
    assert "no data" in out


def test_invalid_json_lines_skipped():
    mixed = "not json\n" + json.dumps({"v": 5}) + "\n"
    code, out = _run(["v", "--bucket-size", "1"], stdin_text=mixed)
    assert code == 0
    assert "total: 1" in out
