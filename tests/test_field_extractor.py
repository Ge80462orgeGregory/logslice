"""Tests for logslice.field_extractor."""
from __future__ import annotations

import pytest

from logslice.field_extractor import (
    FieldExtractorError,
    _flatten,
    flatten_record,
    extract_field,
    extract_fields,
)


# ---------------------------------------------------------------------------
# _flatten (internal)
# ---------------------------------------------------------------------------

def test_flatten_simple_dict():
    result: dict = {}
    _flatten({"a": 1, "b": 2}, "", ".", result)
    assert result == {"a": 1, "b": 2}


def test_flatten_nested_dict():
    result: dict = {}
    _flatten({"a": {"b": 3}}, "", ".", result)
    assert result == {"a.b": 3}


def test_flatten_deeply_nested():
    result: dict = {}
    _flatten({"x": {"y": {"z": "deep"}}}, "", ".", result)
    assert result == {"x.y.z": "deep"}


def test_flatten_list_values():
    result: dict = {}
    _flatten({"items": [10, 20]}, "", ".", result)
    assert result["items.0"] == 10
    assert result["items.1"] == 20


def test_flatten_non_dict_raises():
    with pytest.raises(FieldExtractorError):
        flatten_record([1, 2, 3])


# ---------------------------------------------------------------------------
# flatten_record
# ---------------------------------------------------------------------------

def test_flatten_record_returns_flat_dict():
    rec = {"level": "info", "ctx": {"user": "alice"}}
    flat = flatten_record(rec)
    assert flat == {"level": "info", "ctx.user": "alice"}


def test_flatten_record_custom_separator():
    rec = {"a": {"b": 99}}
    flat = flatten_record(rec, separator="/")
    assert flat == {"a/b": 99}


def test_flatten_record_with_prefix():
    rec = {"k": "v"}
    flat = flatten_record(rec, prefix="log")
    assert "log.k" in flat
    assert flat["log.k"] == "v"


def test_flatten_record_scalar_values_preserved():
    rec = {"count": 5, "active": True, "name": None}
    flat = flatten_record(rec)
    assert flat == {"count": 5, "active": True, "name": None}


# ---------------------------------------------------------------------------
# extract_field
# ---------------------------------------------------------------------------

def test_extract_field_top_level():
    assert extract_field({"a": 1}, "a") == 1


def test_extract_field_nested():
    rec = {"a": {"b": {"c": "found"}}}
    assert extract_field(rec, "a.b.c") == "found"


def test_extract_field_missing_raises():
    with pytest.raises(FieldExtractorError, match="not found"):
        extract_field({"x": 1}, "y")


def test_extract_field_non_dict_traversal_raises():
    with pytest.raises(FieldExtractorError):
        extract_field({"a": 42}, "a.b")


# ---------------------------------------------------------------------------
# extract_fields
# ---------------------------------------------------------------------------

def test_extract_fields_returns_mapping():
    rec = {"a": 1, "b": 2}
    result = extract_fields(rec, ["a", "b"])
    assert result == {"a": 1, "b": 2}


def test_extract_fields_missing_raises_by_default():
    with pytest.raises(FieldExtractorError):
        extract_fields({"a": 1}, ["a", "missing"])


def test_extract_fields_skip_missing():
    rec = {"a": 1}
    result = extract_fields(rec, ["a", "nope"], skip_missing=True)
    assert result == {"a": 1}
