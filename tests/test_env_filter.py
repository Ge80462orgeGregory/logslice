"""Tests for logslice.env_filter and logslice.env_filter_cli."""

from __future__ import annotations

import io
import json

import pytest

from logslice.env_filter import EnvFilter, EnvFilterError
from logslice.env_filter_cli import run_env_filter_cli


# ---------------------------------------------------------------------------
# EnvFilter unit tests
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(EnvFilterError, match="field"):
        EnvFilter(field="", envs=["prod"])


def test_blank_field_raises():
    with pytest.raises(EnvFilterError, match="field"):
        EnvFilter(field="   ", envs=["prod"])


def test_no_envs_raises():
    with pytest.raises(EnvFilterError, match="at least one"):
        EnvFilter(field="env", envs=[])


def test_blank_env_name_raises():
    with pytest.raises(EnvFilterError, match="non-empty"):
        EnvFilter(field="env", envs=["prod", ""])


def test_valid_construction():
    f = EnvFilter(field="env", envs=["prod", "staging"])
    assert f.field == "env"
    assert "prod" in f.envs
    assert "staging" in f.envs
    assert f.invert is False
    assert f.case_sensitive is True


def test_matching_record_kept():
    f = EnvFilter(field="env", envs=["prod"])
    assert f.matches({"env": "prod", "msg": "ok"}) is True


def test_non_matching_record_dropped():
    f = EnvFilter(field="env", envs=["prod"])
    assert f.matches({"env": "dev", "msg": "ok"}) is False


def test_missing_field_dropped():
    f = EnvFilter(field="env", envs=["prod"])
    assert f.matches({"msg": "no env here"}) is False


def test_invert_drops_matching():
    f = EnvFilter(field="env", envs=["prod"], invert=True)
    assert f.matches({"env": "prod"}) is False


def test_invert_keeps_non_matching():
    f = EnvFilter(field="env", envs=["prod"], invert=True)
    assert f.matches({"env": "dev"}) is True


def test_case_insensitive_match():
    f = EnvFilter(field="env", envs=["PROD"], case_sensitive=False)
    assert f.matches({"env": "prod"}) is True


def test_case_sensitive_no_match():
    f = EnvFilter(field="env", envs=["PROD"], case_sensitive=True)
    assert f.matches({"env": "prod"}) is False


def test_nested_field():
    f = EnvFilter(field="meta.env", envs=["staging"])
    assert f.matches({"meta": {"env": "staging"}}) is True
    assert f.matches({"meta": {"env": "prod"}}) is False


def test_filter_iterator():
    f = EnvFilter(field="env", envs=["prod"])
    records = [
        {"env": "prod", "id": 1},
        {"env": "dev", "id": 2},
        {"env": "prod", "id": 3},
    ]
    result = list(f.filter(records))
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 3


def test_non_dict_record_raises():
    f = EnvFilter(field="env", envs=["prod"])
    with pytest.raises(EnvFilterError):
        f.matches(["not", "a", "dict"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

def _make_lines(*records):
    return io.StringIO("\n".join(json.dumps(r) for r in records) + "\n")


def _run(args, lines):
    out = io.StringIO()
    code = run_env_filter_cli(args, stdin=lines, stdout=out)
    return code, out.getvalue().strip().splitlines()


def test_cli_filters_by_env():
    lines = _make_lines(
        {"env": "prod", "id": 1},
        {"env": "dev", "id": 2},
    )
    code, output = _run(["--field", "env", "--envs", "prod"], lines)
    assert code == 0
    assert len(output) == 1
    assert json.loads(output[0])["id"] == 1


def test_cli_invert_flag():
    lines = _make_lines(
        {"env": "prod", "id": 1},
        {"env": "dev", "id": 2},
    )
    code, output = _run(["--field", "env", "--envs", "prod", "--invert"], lines)
    assert code == 0
    assert len(output) == 1
    assert json.loads(output[0])["id"] == 2


def test_cli_missing_field_exits_2():
    lines = _make_lines({"env": "prod"})
    code, _ = _run(["--envs", "prod"], lines)
    assert code == 2


def test_cli_ignore_case():
    lines = _make_lines({"env": "PROD", "id": 1}, {"env": "dev", "id": 2})
    code, output = _run(["--field", "env", "--envs", "prod", "--ignore-case"], lines)
    assert code == 0
    assert len(output) == 1
    assert json.loads(output[0])["id"] == 1
