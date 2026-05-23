"""Tests for logslice.type_coerce and type_coerce_cli."""

from __future__ import annotations

import json
import textwrap

import pytest

from logslice.type_coerce import TypeCoerceError, TypeCoercer, _coerce
from logslice.type_coerce_cli import run_type_coerce_cli


# ---------------------------------------------------------------------------
# TypeCoercer construction
# ---------------------------------------------------------------------------

def test_empty_rules_raises():
    with pytest.raises(TypeCoerceError, match="rules must not be empty"):
        TypeCoercer({})


def test_blank_field_raises():
    with pytest.raises(TypeCoerceError, match="field name must not be blank"):
        TypeCoercer({"  ": "int"})


def test_unknown_type_raises():
    with pytest.raises(TypeCoerceError, match="unknown type"):
        TypeCoercer({"level": "integer"})


def test_valid_construction():
    c = TypeCoercer({"status": "int", "score": "float"})
    assert c.rules == {"status": "int", "score": "float"}
    assert c.skip_errors is False


# ---------------------------------------------------------------------------
# _coerce helper
# ---------------------------------------------------------------------------

def test_coerce_str_to_int():
    assert _coerce("42", "int") == 42


def test_coerce_float_str_to_int_truncates():
    assert _coerce("3.9", "int") == 3


def test_coerce_to_float():
    assert _coerce("1.5", "float") == 1.5


def test_coerce_to_str():
    assert _coerce(99, "str") == "99"


def test_coerce_bool_true_strings():
    for v in ("true", "True", "1", "yes"):
        assert _coerce(v, "bool") is True


def test_coerce_bool_false_strings():
    for v in ("false", "False", "0", "no"):
        assert _coerce(v, "bool") is False


def test_coerce_bool_invalid_string_raises():
    with pytest.raises(ValueError):
        _coerce("maybe", "bool")


# ---------------------------------------------------------------------------
# TypeCoercer.coerce
# ---------------------------------------------------------------------------

def test_coerce_simple_field():
    c = TypeCoercer({"status": "int"})
    result = c.coerce({"status": "200", "msg": "ok"})
    assert result == {"status": 200, "msg": "ok"}


def test_coerce_does_not_mutate_original():
    c = TypeCoercer({"status": "int"})
    original = {"status": "404"}
    c.coerce(original)
    assert original["status"] == "404"


def test_coerce_nested_field():
    c = TypeCoercer({"http.code": "int"})
    result = c.coerce({"http": {"code": "500"}})
    assert result["http"]["code"] == 500


def test_missing_field_skipped_silently():
    c = TypeCoercer({"missing": "int"})
    result = c.coerce({"other": "x"})
    assert result == {"other": "x"}


def test_coerce_error_raises_by_default():
    c = TypeCoercer({"val": "int"})
    with pytest.raises(TypeCoerceError, match="cannot coerce"):
        c.coerce({"val": "not-a-number"})


def test_coerce_error_skipped_when_skip_errors():
    c = TypeCoercer({"val": "int"}, skip_errors=True)
    result = c.coerce({"val": "not-a-number"})
    assert result["val"] == "not-a-number"


def test_non_dict_record_raises():
    c = TypeCoercer({"x": "int"})
    with pytest.raises(TypeCoerceError, match="must be a dict"):
        c.coerce([1, 2, 3])  # type: ignore


def test_coerce_many():
    c = TypeCoercer({"n": "float"})
    records = [{"n": "1"}, {"n": "2"}, {"n": "3"}]
    results = c.coerce_many(records)
    assert [r["n"] for r in results] == [1.0, 2.0, 3.0]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _run(lines, extra_args=None):
    import io, unittest.mock as mock
    text = "\n".join(lines) + "\n"
    with mock.patch("sys.stdin", io.StringIO(text)):
        captured = io.StringIO()
        with mock.patch("sys.stdout", captured):
            code = run_type_coerce_cli(extra_args or [])
    return code, captured.getvalue().splitlines()


def test_cli_coerces_field():
    lines = [json.dumps({"status": "200"})]
    code, out = _run(lines, ["--field", "status:int"])
    assert code == 0
    assert json.loads(out[0])["status"] == 200


def test_cli_invalid_rule_exits_2():
    code, _ = _run([], ["--field", "badformat"])
    assert code == 2


def test_cli_unknown_type_exits_2():
    code, _ = _run([], ["--field", "x:uuid"])
    assert code == 2


def test_cli_non_json_line_passed_through():
    lines = ["not json at all"]
    code, out = _run(lines, ["--field", "x:int"])
    assert code == 0
    assert out[0] == "not json at all"


def test_cli_skip_errors_flag():
    lines = [json.dumps({"val": "oops"})]
    code, out = _run(lines, ["--field", "val:int", "--skip-errors"])
    assert code == 0
    assert json.loads(out[0])["val"] == "oops"
