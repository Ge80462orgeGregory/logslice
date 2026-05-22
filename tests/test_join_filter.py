"""Tests for logslice.join_filter and logslice.join_cli."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import List

import pytest

from logslice.join_filter import JoinError, JoinFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lines(*records) -> List[str]:
    return [json.dumps(r) for r in records]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_empty_key_raises():
    with pytest.raises(JoinError, match="non-empty"):
        JoinFilter(key="", right_lines=[])


def test_index_size_reflects_right_lines():
    right = _lines({"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"})
    jf = JoinFilter(key="id", right_lines=right)
    assert jf.index_size == 2


def test_invalid_json_in_right_skipped():
    right = ["not-json\n", json.dumps({"id": "1", "x": 9})]
    jf = JoinFilter(key="id", right_lines=right)
    assert jf.index_size == 1


def test_non_dict_right_record_skipped():
    right = [json.dumps([1, 2, 3]), json.dumps({"id": "a", "v": 1})]
    jf = JoinFilter(key="id", right_lines=right)
    assert jf.index_size == 1


# ---------------------------------------------------------------------------
# join_record
# ---------------------------------------------------------------------------

def test_join_merges_fields():
    right = _lines({"id": "42", "region": "eu"})
    jf = JoinFilter(key="id", right_lines=right)
    result = jf.join_record({"id": "42", "level": "info"})
    assert result["joined_region"] == "eu"
    assert result["level"] == "info"


def test_join_no_match_returns_original():
    right = _lines({"id": "99", "region": "us"})
    jf = JoinFilter(key="id", right_lines=right)
    original = {"id": "1", "msg": "hello"}
    result = jf.join_record(original)
    assert result == original
    assert "joined_region" not in result


def test_join_does_not_mutate_original():
    right = _lines({"id": "1", "extra": "data"})
    jf = JoinFilter(key="id", right_lines=right)
    original = {"id": "1", "msg": "hi"}
    jf.join_record(original)
    assert "joined_extra" not in original


def test_join_non_dict_record_raises():
    jf = JoinFilter(key="id", right_lines=[])
    with pytest.raises(JoinError):
        jf.join_record(["not", "a", "dict"])  # type: ignore[arg-type]


def test_custom_prefix_applied():
    right = _lines({"id": "7", "score": 100})
    jf = JoinFilter(key="id", right_lines=right, prefix="r_")
    result = jf.join_record({"id": "7"})
    assert "r_score" in result
    assert "joined_score" not in result


def test_nested_key_resolved():
    right = _lines({"meta": {"id": "abc"}, "tag": "prod"})
    jf = JoinFilter(key="meta.id", right_lines=right)
    result = jf.join_record({"meta": {"id": "abc"}, "level": "warn"})
    assert result["joined_tag"] == "prod"


# ---------------------------------------------------------------------------
# process (streaming)
# ---------------------------------------------------------------------------

def test_process_yields_json_strings():
    right = _lines({"id": "1", "env": "prod"})
    jf = JoinFilter(key="id", right_lines=right)
    primary = _lines({"id": "1", "msg": "ok"}, {"id": "2", "msg": "nope"})
    results = list(jf.process(primary))
    assert len(results) == 2
    first = json.loads(results[0])
    assert first["joined_env"] == "prod"
    second = json.loads(results[1])
    assert "joined_env" not in second


def test_process_skips_blank_lines():
    right = _lines({"id": "1", "x": 1})
    jf = JoinFilter(key="id", right_lines=right)
    primary = [json.dumps({"id": "1"}), "", "   "]
    results = list(jf.process(primary))
    assert len(results) == 1


def test_process_skips_invalid_json():
    jf = JoinFilter(key="id", right_lines=[])
    primary = ["bad-json", json.dumps({"id": "1"})]
    results = list(jf.process(primary))
    assert len(results) == 1
