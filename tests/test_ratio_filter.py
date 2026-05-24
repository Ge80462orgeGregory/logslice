"""Tests for RatioFilter and its CLI."""

from __future__ import annotations

import json
import pytest
from io import StringIO
from unittest.mock import patch

from logslice.ratio_filter import RatioFilter, RatioFilterError
from logslice.ratio_filter_cli import run_ratio_filter_cli


# ── construction errors ───────────────────────────────────────────────────────

def test_empty_numerator_raises():
    with pytest.raises(RatioFilterError, match="numerator"):
        RatioFilter("", "denominator", min_val=0.5)


def test_empty_denominator_raises():
    with pytest.raises(RatioFilterError, match="denominator"):
        RatioFilter("a", "", min_val=0.5)


def test_no_bounds_raises():
    with pytest.raises(RatioFilterError, match="at least one"):
        RatioFilter("a", "b")


def test_min_exceeds_max_raises():
    with pytest.raises(RatioFilterError, match="min_val must not exceed"):
        RatioFilter("a", "b", min_val=2.0, max_val=1.0)


# ── property accessors ────────────────────────────────────────────────────────

def test_properties_stored():
    f = RatioFilter("errors", "total", min_val=0.1, max_val=0.9, invert=True)
    assert f.numerator == "errors"
    assert f.denominator == "total"
    assert f.min_val == 0.1
    assert f.max_val == 0.9
    assert f.invert is True


# ── matching logic ────────────────────────────────────────────────────────────

def test_ratio_within_range_matches():
    f = RatioFilter("a", "b", min_val=0.4, max_val=0.6)
    assert f.matches({"a": 5, "b": 10}) is True


def test_ratio_below_min_excluded():
    f = RatioFilter("a", "b", min_val=0.5)
    assert f.matches({"a": 1, "b": 10}) is False


def test_ratio_above_max_excluded():
    f = RatioFilter("a", "b", max_val=0.5)
    assert f.matches({"a": 9, "b": 10}) is False


def test_zero_denominator_excluded():
    f = RatioFilter("a", "b", min_val=0.0)
    assert f.matches({"a": 5, "b": 0}) is False


def test_missing_numerator_field_excluded():
    f = RatioFilter("x", "b", min_val=0.0)
    assert f.matches({"b": 10}) is False


def test_non_numeric_value_excluded():
    f = RatioFilter("a", "b", min_val=0.0)
    assert f.matches({"a": "hello", "b": 10}) is False


def test_invert_flips_result():
    f = RatioFilter("a", "b", min_val=0.5, invert=True)
    assert f.matches({"a": 1, "b": 10}) is True   # ratio=0.1, normally excluded
    assert f.matches({"a": 8, "b": 10}) is False  # ratio=0.8, normally included


def test_nested_fields():
    f = RatioFilter("metrics.errors", "metrics.total", min_val=0.1)
    assert f.matches({"metrics": {"errors": 3, "total": 10}}) is True


def test_non_dict_record_returns_false():
    f = RatioFilter("a", "b", min_val=0.0)
    assert f.matches([1, 2, 3]) is False  # type: ignore[arg-type]


# ── CLI ───────────────────────────────────────────────────────────────────────

def _run(lines, argv):
    stdin = StringIO("\n".join(lines) + "\n")
    captured = []
    with patch("sys.stdin", stdin), patch("builtins.print", side_effect=lambda *a, **k: captured.append(a[0])):
        code = run_ratio_filter_cli(argv)
    return code, captured


def test_cli_missing_numerator_exits_2():
    code, _ = _run([], ["--denominator", "b", "--min", "0.5"])
    assert code == 2


def test_cli_no_bounds_exits_2():
    code, _ = _run([], ["--numerator", "a", "--denominator", "b"])
    assert code == 2


def test_cli_filters_matching_records():
    lines = [
        json.dumps({"a": 5, "b": 10}),   # ratio=0.5, passes min=0.4
        json.dumps({"a": 1, "b": 10}),   # ratio=0.1, excluded
    ]
    code, out = _run(lines, ["--numerator", "a", "--denominator", "b", "--min", "0.4"])
    assert code == 0
    assert len(out) == 1
    assert json.loads(out[0])["a"] == 5
