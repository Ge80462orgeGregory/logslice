"""Tests for PrefixFilter and the prefix CLI."""

from __future__ import annotations

import json
import pytest

from logslice.prefix_filter import PrefixFilter, PrefixFilterError
from logslice.prefix_cli import build_prefix_parser, run_prefix_cli


# ---------------------------------------------------------------------------
# PrefixFilter unit tests
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(PrefixFilterError):
        PrefixFilter(field="", prefix="err")


def test_blank_field_raises():
    with pytest.raises(PrefixFilterError):
        PrefixFilter(field="   ", prefix="err")


def test_none_prefix_raises():
    with pytest.raises(PrefixFilterError):
        PrefixFilter(field="msg", prefix=None)  # type: ignore[arg-type]


def test_field_property():
    pf = PrefixFilter(field="level", prefix="err")
    assert pf.field == "level"


def test_prefix_property():
    pf = PrefixFilter(field="level", prefix="warn")
    assert pf.prefix == "warn"


def test_invert_default_false():
    pf = PrefixFilter(field="level", prefix="err")
    assert pf.invert is False


def test_case_sensitive_default_true():
    pf = PrefixFilter(field="level", prefix="ERR")
    assert pf.case_sensitive is True


def test_matches_simple_prefix():
    pf = PrefixFilter(field="msg", prefix="ERROR")
    assert pf.matches({"msg": "ERROR: something went wrong"}) is True


def test_no_match_returns_false():
    pf = PrefixFilter(field="msg", prefix="ERROR")
    assert pf.matches({"msg": "INFO: all good"}) is False


def test_invert_flips_result():
    pf = PrefixFilter(field="msg", prefix="ERROR", invert=True)
    assert pf.matches({"msg": "INFO: all good"}) is True
    assert pf.matches({"msg": "ERROR: boom"}) is False


def test_case_insensitive_match():
    pf = PrefixFilter(field="level", prefix="err", case_sensitive=False)
    assert pf.matches({"level": "ERROR"}) is True


def test_case_sensitive_no_match_on_wrong_case():
    pf = PrefixFilter(field="level", prefix="err", case_sensitive=True)
    assert pf.matches({"level": "ERROR"}) is False


def test_missing_field_returns_false():
    pf = PrefixFilter(field="msg", prefix="ERROR")
    assert pf.matches({"level": "info"}) is False


def test_nested_field():
    pf = PrefixFilter(field="http.path", prefix="/api")
    assert pf.matches({"http": {"path": "/api/v1/users"}}) is True
    assert pf.matches({"http": {"path": "/health"}}) is False


def test_non_string_field_returns_false():
    pf = PrefixFilter(field="code", prefix="4")
    assert pf.matches({"code": 404}) is False


def test_non_dict_record_raises():
    pf = PrefixFilter(field="msg", prefix="err")
    with pytest.raises(PrefixFilterError):
        pf.matches(["not", "a", "dict"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

def _run(args_list, lines):
    parser = build_prefix_parser()
    args = parser.parse_args(args_list)
    return run_prefix_cli(args, lines=lines)


def _make_lines(*records):
    return [json.dumps(r) for r in records]


def test_cli_keeps_matching_lines(capsys):
    lines = _make_lines(
        {"msg": "ERROR: disk full"},
        {"msg": "INFO: started"},
        {"msg": "ERROR: oom"},
    )
    rc = _run(["--field", "msg", "--prefix", "ERROR"], lines)
    assert rc == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 2
    assert all(json.loads(l)["msg"].startswith("ERROR") for l in out)


def test_cli_invert_drops_matching_lines(capsys):
    lines = _make_lines({"msg": "ERROR: x"}, {"msg": "INFO: y"})
    rc = _run(["--field", "msg", "--prefix", "ERROR", "--invert"], lines)
    assert rc == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1
    assert json.loads(out[0])["msg"] == "INFO: y"


def test_cli_ignore_case(capsys):
    lines = _make_lines({"level": "Error"}, {"level": "info"})
    rc = _run(["--field", "level", "--prefix", "err", "--ignore-case"], lines)
    assert rc == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1


def test_cli_missing_field_exits_2(capsys):
    parser = build_prefix_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--prefix", "err"])
    assert exc_info.value.code != 0


def test_cli_invalid_json_lines_skipped(capsys):
    lines = ["not json\n", json.dumps({"msg": "ERROR: ok"})]
    rc = _run(["--field", "msg", "--prefix", "ERROR"], lines)
    assert rc == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1
