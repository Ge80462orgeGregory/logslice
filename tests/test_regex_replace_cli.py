"""Integration tests for the regex-replace CLI."""

from __future__ import annotations

import json
from io import StringIO
from typing import List
from unittest.mock import patch

import pytest

from logslice.regex_replace_cli import run_regex_replace_cli


def _make_lines(records: List[dict]) -> str:
    return "\n".join(json.dumps(r) for r in records) + "\n"


def _run(argv: List[str], stdin_text: str):
    with patch("sys.stdin", StringIO(stdin_text)):
        return run_regex_replace_cli(argv)


def test_missing_field_exits_2():
    code = _run(["--pattern", r"\d+", "--replacement", "N"], "")
    assert code == 2


def test_missing_pattern_exits_2():
    code = _run(["--field", "msg"], "")
    assert code == 2


def test_invalid_pattern_exits_2():
    code = _run(["--field", "msg", "--pattern", "[bad", "--replacement", "X"], "")
    assert code == 2


def test_basic_substitution(capsys):
    lines = _make_lines([{"msg": "error 42"}, {"msg": "ok"}])
    code = _run(["--field", "msg", "--pattern", r"\d+", "--replacement", "NUM"], lines)
    assert code == 0
    out = capsys.readouterr().out
    records = [json.loads(l) for l in out.strip().splitlines()]
    assert records[0]["msg"] == "error NUM"
    assert records[1]["msg"] == "ok"


def test_count_limits_replacements(capsys):
    lines = _make_lines([{"msg": "1 2 3"}])
    code = _run(
        ["--field", "msg", "--pattern", r"\d", "--replacement", "N", "--count", "2"],
        lines,
    )
    assert code == 0
    out = capsys.readouterr().out
    assert json.loads(out.strip())["msg"] == "N N 3"


def test_non_json_line_passes_through(capsys):
    code = _run(
        ["--field", "msg", "--pattern", r"x", "--replacement", "y"],
        "not json at all\n",
    )
    assert code == 0
    out = capsys.readouterr().out
    assert out.strip() == "not json at all"


def test_blank_lines_skipped(capsys):
    lines = "\n\n" + json.dumps({"msg": "hello 1"}) + "\n"
    code = _run(["--field", "msg", "--pattern", r"\d", "--replacement", "#"], lines)
    assert code == 0
    out = capsys.readouterr().out
    assert len(out.strip().splitlines()) == 1
