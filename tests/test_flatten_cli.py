"""Tests for logslice.flatten_cli."""
from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from logslice.flatten_cli import run_flatten_cli


def _run(lines: list[str], extra_argv: list[str] | None = None) -> tuple[int, list[str]]:
    """Run the CLI with *lines* on stdin, return (exit_code, stdout_lines)."""
    argv = extra_argv or []
    stdin_data = "\n".join(lines) + "\n"
    captured: list[str] = []

    def fake_print(msg="", **_kw):
        captured.append(str(msg))

    with patch("sys.stdin", StringIO(stdin_data)):
        with patch("builtins.print", side_effect=fake_print):
            code = run_flatten_cli(argv)
    return code, captured


def _make_lines(*records) -> list[str]:
    return [json.dumps(r) for r in records]


def test_flat_record_unchanged():
    lines = _make_lines({"level": "info", "msg": "hello"})
    code, out = _run(lines)
    assert code == 0
    assert len(out) == 1
    assert json.loads(out[0]) == {"level": "info", "msg": "hello"}


def test_nested_record_flattened():
    lines = _make_lines({"a": {"b": {"c": 42}}})
    code, out = _run(lines)
    assert code == 0
    assert json.loads(out[0]) == {"a.b.c": 42}


def test_custom_separator():
    lines = _make_lines({"x": {"y": 1}})
    code, out = _run(lines, ["--separator", "_"])
    assert code == 0
    assert json.loads(out[0]) == {"x_y": 1}


def test_list_values_indexed():
    lines = _make_lines({"tags": ["a", "b"]})
    code, out = _run(lines)
    assert code == 0
    result = json.loads(out[0])
    assert result["tags.0"] == "a"
    assert result["tags.1"] == "b"


def test_invalid_json_returns_1():
    code, _ = _run(["not-json"])
    assert code == 1


def test_invalid_json_skip_invalid():
    lines = ["not-json", json.dumps({"ok": 1})]
    code, out = _run(lines, ["--skip-invalid"])
    assert code == 0
    assert len(out) == 1
    assert json.loads(out[0]) == {"ok": 1}


def test_empty_lines_skipped():
    lines = ["", json.dumps({"k": "v"}), ""]
    code, out = _run(lines)
    assert code == 0
    assert len(out) == 1


def test_multiple_records_all_flattened():
    lines = _make_lines(
        {"a": {"b": 1}},
        {"c": {"d": 2}},
    )
    code, out = _run(lines)
    assert code == 0
    assert json.loads(out[0]) == {"a.b": 1}
    assert json.loads(out[1]) == {"c.d": 2}
