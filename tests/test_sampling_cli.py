"""Tests for logslice.sampling_cli."""

from __future__ import annotations

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from logslice.sampling_cli import build_sampling_parser, run_sampling_cli


def _run(argv: list[str], stdin_lines: list[str]) -> tuple[int, list[dict]]:
    """Run the CLI with patched stdin; return (exit_code, parsed_output_lines)."""
    parser = build_sampling_parser()
    args = parser.parse_args(argv)
    fake_stdin = StringIO("\n".join(stdin_lines) + "\n")
    captured: list[str] = []

    with patch("sys.stdin", fake_stdin), patch("builtins.print", side_effect=lambda *a, **kw: captured.append(str(a[0])) if not kw.get("file") else None):
        code = run_sampling_cli(args)

    records = []
    for line in captured:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return code, records


def _make_lines(n: int) -> list[str]:
    return [json.dumps({"seq": i}) for i in range(n)]


def test_every_n_keeps_every_second():
    lines = _make_lines(10)
    code, records = _run(["--every-n", "2"], lines)
    assert code == 0
    assert len(records) == 5
    assert records[0]["seq"] == 1


def test_fraction_one_keeps_all():
    lines = _make_lines(8)
    code, records = _run(["--fraction", "1.0", "--seed", "0"], lines)
    assert code == 0
    assert len(records) == 8


def test_invalid_fraction_returns_exit_2():
    parser = build_sampling_parser()
    args = parser.parse_args(["--fraction", "2.0"])
    code = run_sampling_cli(args)
    assert code == 2


def test_invalid_every_n_returns_exit_2():
    parser = build_sampling_parser()
    args = parser.parse_args(["--every-n", "0"])
    code = run_sampling_cli(args)
    assert code == 2


def test_non_json_lines_skipped():
    lines = ["not json", json.dumps({"ok": True}), "also not json"]
    code, records = _run(["--every-n", "1"], lines)
    assert code == 0
    assert records == [{"ok": True}]


def test_empty_lines_skipped():
    lines = ["", "   ", json.dumps({"x": 1})]
    code, records = _run(["--every-n", "1"], lines)
    assert code == 0
    assert len(records) == 1


def test_stats_flag_writes_to_stderr(capsys):
    parser = build_sampling_parser()
    args = parser.parse_args(["--every-n", "1", "--stats"])
    fake_stdin = StringIO(json.dumps({"a": 1}) + "\n")
    with patch("sys.stdin", fake_stdin):
        run_sampling_cli(args)
    captured = capsys.readouterr()
    assert "seen=1" in captured.err
    assert "emitted=1" in captured.err
