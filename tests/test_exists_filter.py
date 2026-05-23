"""Tests for ExistsFilter and the exists CLI."""

from __future__ import annotations

import json
from typing import List

import pytest

from logslice.exists_filter import ExistsFilter, ExistsFilterError
from logslice.exists_cli import build_exists_parser, run_exists_cli


# ---------------------------------------------------------------------------
# ExistsFilter unit tests
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(ExistsFilterError):
        ExistsFilter("")


def test_blank_field_raises():
    with pytest.raises(ExistsFilterError):
        ExistsFilter("   ")


def test_field_property():
    f = ExistsFilter("user.id")
    assert f.field == "user.id"


def test_require_non_null_default_true():
    f = ExistsFilter("x")
    assert f.require_non_null is True


def test_invert_default_false():
    f = ExistsFilter("x")
    assert f.invert is False


def test_keep_present_non_null():
    f = ExistsFilter("level")
    assert f.keep({"level": "info"}) is True


def test_drop_missing_field():
    f = ExistsFilter("level")
    assert f.keep({"msg": "hello"}) is False


def test_drop_null_field_by_default():
    f = ExistsFilter("level")
    assert f.keep({"level": None}) is False


def test_allow_null_keeps_null_field():
    f = ExistsFilter("level", require_non_null=False)
    assert f.keep({"level": None}) is True


def test_allow_null_drops_missing_field():
    f = ExistsFilter("level", require_non_null=False)
    assert f.keep({"msg": "hi"}) is False


def test_invert_drops_present_field():
    f = ExistsFilter("level", invert=True)
    assert f.keep({"level": "error"}) is False


def test_invert_keeps_missing_field():
    f = ExistsFilter("level", invert=True)
    assert f.keep({"msg": "hi"}) is True


def test_nested_field_present():
    f = ExistsFilter("user.id")
    assert f.keep({"user": {"id": 42}}) is True


def test_nested_field_missing_parent():
    f = ExistsFilter("user.id")
    assert f.keep({"msg": "x"}) is False


def test_non_dict_record_raises():
    f = ExistsFilter("level")
    with pytest.raises(ExistsFilterError):
        f.keep(["not", "a", "dict"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _make_lines(records: List[dict]) -> List[str]:
    return [json.dumps(r) for r in records]


def _run(argv: List[str], lines: List[str]) -> tuple[int, List[str], List[str]]:
    import io, sys
    parser = build_exists_parser()
    args = parser.parse_args(argv)
    captured: List[str] = []
    original_print = __builtins__["print"] if isinstance(__builtins__, dict) else print  # noqa

    import builtins
    printed: List[str] = []

    def fake_print(*a, **kw):
        if kw.get("file") is sys.stderr:
            return
        printed.append(" ".join(str(x) for x in a))

    monkeypatch_print = builtins.print
    builtins.print = fake_print  # type: ignore[assignment]
    try:
        code = run_exists_cli(args, lines=lines)
    finally:
        builtins.print = monkeypatch_print
    return code, printed


def test_cli_keeps_records_with_field():
    lines = _make_lines([{"level": "info"}, {"msg": "no level"}])
    code, out = _run(["level"], lines)
    assert code == 0
    assert len(out) == 1
    assert json.loads(out[0])["level"] == "info"


def test_cli_invert_drops_records_with_field():
    lines = _make_lines([{"level": "info"}, {"msg": "no level"}])
    code, out = _run(["level", "--invert"], lines)
    assert code == 0
    assert len(out) == 1
    assert "level" not in json.loads(out[0])


def test_cli_invalid_field_returns_exit_2():
    code, _ = _run([""], [])
    assert code == 2
