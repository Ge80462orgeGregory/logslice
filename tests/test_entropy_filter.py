"""Tests for EntropyFilter and entropy_filter_cli."""

from __future__ import annotations

import json
import math
from collections import Counter
from io import StringIO
from typing import List
from unittest.mock import patch

import pytest

from logslice.entropy_filter import EntropyFilter, EntropyFilterError, _shannon_entropy
from logslice.entropy_filter_cli import run_entropy_cli


# ---------------------------------------------------------------------------
# _shannon_entropy helpers
# ---------------------------------------------------------------------------

def test_entropy_empty_string_is_zero():
    assert _shannon_entropy("") == 0.0


def test_entropy_single_char_is_zero():
    assert _shannon_entropy("aaaa") == pytest.approx(0.0)


def test_entropy_two_equal_chars():
    # "ab" repeated — each char prob 0.5, entropy = 1.0
    assert _shannon_entropy("abab") == pytest.approx(1.0)


def test_entropy_increases_with_diversity():
    low = _shannon_entropy("aaab")
    high = _shannon_entropy("abcd")
    assert high > low


# ---------------------------------------------------------------------------
# EntropyFilter construction errors
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(EntropyFilterError):
        EntropyFilter(field="", min_entropy=1.0)


def test_blank_field_raises():
    with pytest.raises(EntropyFilterError):
        EntropyFilter(field="   ", min_entropy=1.0)


def test_no_bounds_raises():
    with pytest.raises(EntropyFilterError):
        EntropyFilter(field="msg")


def test_negative_min_raises():
    with pytest.raises(EntropyFilterError):
        EntropyFilter(field="msg", min_entropy=-0.1)


def test_negative_max_raises():
    with pytest.raises(EntropyFilterError):
        EntropyFilter(field="msg", max_entropy=-1.0)


def test_min_exceeds_max_raises():
    with pytest.raises(EntropyFilterError):
        EntropyFilter(field="msg", min_entropy=3.0, max_entropy=1.0)


# ---------------------------------------------------------------------------
# EntropyFilter.matches
# ---------------------------------------------------------------------------

def test_matches_within_range():
    f = EntropyFilter(field="msg", min_entropy=0.5, max_entropy=3.0)
    assert f.matches({"msg": "abcd"}) is True


def test_rejects_below_min():
    f = EntropyFilter(field="msg", min_entropy=2.0)
    assert f.matches({"msg": "aaaa"}) is False


def test_rejects_above_max():
    f = EntropyFilter(field="msg", max_entropy=0.5)
    assert f.matches({"msg": "abcdefgh"}) is False


def test_invert_flips_result():
    f = EntropyFilter(field="msg", min_entropy=2.0, invert=True)
    # low-entropy string normally rejected, invert => accepted
    assert f.matches({"msg": "aaaa"}) is True


def test_non_string_field_returns_false():
    f = EntropyFilter(field="count", min_entropy=0.0)
    assert f.matches({"count": 42}) is False


def test_missing_field_returns_false():
    f = EntropyFilter(field="missing", min_entropy=0.0)
    assert f.matches({"other": "hello"}) is False


def test_nested_field_supported():
    f = EntropyFilter(field="data.token", min_entropy=1.0)
    assert f.matches({"data": {"token": "abab"}}) is True


def test_non_dict_record_raises():
    f = EntropyFilter(field="msg", min_entropy=0.0)
    with pytest.raises(EntropyFilterError):
        f.matches(["not", "a", "dict"])  # type: ignore


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_lines(records: List[dict]) -> str:
    return "\n".join(json.dumps(r) for r in records) + "\n"


def _run(argv: List[str], stdin_text: str):
    with patch("sys.stdin", StringIO(stdin_text)):
        captured: List[str] = []
        with patch("builtins.print", side_effect=lambda *a, **kw: captured.append(str(a[0]))):
            code = run_entropy_cli(argv)
    return code, captured


def test_cli_missing_field_exits_2():
    code, _ = _run(["--min", "1.0"], "")
    assert code == 2


def test_cli_no_bounds_exits_2():
    code, _ = _run(["--field", "msg"], "")
    assert code == 2


def test_cli_keeps_matching_record():
    lines = _make_lines([{"msg": "abcd"}, {"msg": "aaaa"}])
    code, out = _run(["--field", "msg", "--min", "1.5"], lines)
    assert code == 0
    assert len(out) == 1
    assert json.loads(out[0])["msg"] == "abcd"


def test_cli_invert_flag():
    lines = _make_lines([{"msg": "abcd"}, {"msg": "aaaa"}])
    code, out = _run(["--field", "msg", "--min", "1.5", "--invert"], lines)
    assert code == 0
    assert len(out) == 1
    assert json.loads(out[0])["msg"] == "aaaa"
