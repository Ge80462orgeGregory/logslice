"""Tests for logslice.label_filter and logslice.label_cli."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import List

import pytest

from logslice.label_filter import LabelFilter, LabelFilterError


# ---------------------------------------------------------------------------
# LabelFilter unit tests
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(LabelFilterError, match="non-empty"):
        LabelFilter(field="", include=["info"])


def test_no_include_or_exclude_raises():
    with pytest.raises(LabelFilterError, match="at least one"):
        LabelFilter(field="level")


def test_include_passes_matching_record():
    f = LabelFilter(field="level", include=["info", "warn"])
    assert f.matches({"level": "info"}) is True


def test_include_drops_non_matching_record():
    f = LabelFilter(field="level", include=["info"])
    assert f.matches({"level": "error"}) is False


def test_exclude_drops_matching_record():
    f = LabelFilter(field="level", exclude=["debug"])
    assert f.matches({"level": "debug"}) is False


def test_exclude_passes_non_matching_record():
    f = LabelFilter(field="level", exclude=["debug"])
    assert f.matches({"level": "info"}) is True


def test_include_and_exclude_combined():
    f = LabelFilter(field="level", include=["info", "warn", "error"], exclude=["warn"])
    assert f.matches({"level": "info"}) is True
    assert f.matches({"level": "warn"}) is False
    assert f.matches({"level": "error"}) is True


def test_missing_field_passes_by_default():
    f = LabelFilter(field="level", include=["info"])
    assert f.matches({"message": "hello"}) is True


def test_missing_field_dropped_when_configured():
    f = LabelFilter(field="level", include=["info"], missing_passes=False)
    assert f.matches({"message": "hello"}) is False


def test_nested_field_dot_notation():
    f = LabelFilter(field="meta.env", include=["prod"])
    assert f.matches({"meta": {"env": "prod"}}) is True
    assert f.matches({"meta": {"env": "staging"}}) is False


def test_non_string_value_coerced():
    f = LabelFilter(field="code", include=["200"])
    assert f.matches({"code": 200}) is True


def test_non_dict_record_raises():
    f = LabelFilter(field="level", include=["info"])
    with pytest.raises(LabelFilterError, match="dict"):
        f.matches(["not", "a", "dict"])  # type: ignore[arg-type]


def test_filter_yields_matching_records():
    f = LabelFilter(field="level", include=["info"])
    records = [
        {"level": "info", "msg": "a"},
        {"level": "debug", "msg": "b"},
        {"level": "info", "msg": "c"},
    ]
    result = list(f.filter(records))
    assert len(result) == 2
    assert result[0]["msg"] == "a"
    assert result[1]["msg"] == "c"


def test_field_and_include_labels_properties():
    f = LabelFilter(field="level", include=["info"], exclude=["debug"])
    assert f.field == "level"
    assert f.include_labels == frozenset(["info"])
    assert f.exclude_labels == frozenset(["debug"])


# ---------------------------------------------------------------------------
# label_cli integration tests
# ---------------------------------------------------------------------------

def _run(lines: List[str], extra_args: List[str]) -> subprocess.CompletedProcess:
    input_data = "\n".join(lines) + "\n"
    return subprocess.run(
        [sys.executable, "-m", "logslice.label_cli"] + extra_args,
        input=input_data,
        capture_output=True,
        text=True,
    )


def _make_lines(records: List[dict]) -> List[str]:
    return [json.dumps(r) for r in records]


def test_cli_include_filters_correctly():
    lines = _make_lines([
        {"level": "info", "msg": "keep"},
        {"level": "debug", "msg": "drop"},
    ])
    result = _run(lines, ["--field", "level", "--include", "info"])
    assert result.returncode == 0
    out_records = [json.loads(l) for l in result.stdout.strip().splitlines()]
    assert len(out_records) == 1
    assert out_records[0]["msg"] == "keep"


def test_cli_exclude_filters_correctly():
    lines = _make_lines([
        {"level": "info", "msg": "keep"},
        {"level": "debug", "msg": "drop"},
    ])
    result = _run(lines, ["--field", "level", "--exclude", "debug"])
    assert result.returncode == 0
    out_records = [json.loads(l) for l in result.stdout.strip().splitlines()]
    assert len(out_records) == 1
    assert out_records[0]["msg"] == "keep"


def test_cli_no_include_or_exclude_exits_2():
    result = _run(['{"level": "info"}'], ["--field", "level"])
    assert result.returncode == 2
