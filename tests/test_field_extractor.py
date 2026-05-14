"""Tests for logslice.field_extractor."""

import pytest

from logslice.field_extractor import (
    FieldExtractorError,
    extract_field,
    extract_fields,
    flatten_record,
)


# ---------------------------------------------------------------------------
# flatten_record
# ---------------------------------------------------------------------------

def test_flatten_simple_dict():
    record = {"level": "info", "msg": "hello"}
    assert flatten_record(record) == {"level": "info", "msg": "hello"}


def test_flatten_nested_dict():
    record = {"http": {"method": "GET", "status": 200}}
    flat = flatten_record(record)
    assert flat["http.method"] == "GET"
    assert flat["http.status"] == 200


def test_flatten_deeply_nested():
    record = {"a": {"b": {"c": 42}}}
    flat = flatten_record(record)
    assert flat["a.b.c"] == 42


def test_flatten_list_values():
    record = {"tags": ["web", "api"]}
    flat = flatten_record(record)
    assert flat["tags.0"] == "web"
    assert flat["tags.1"] == "api"


def test_flatten_non_dict_raises():
    with pytest.raises(FieldExtractorError, match="Expected a dict record"):
        flatten_record(["not", "a", "dict"])  # type: ignore[arg-type]


def test_flatten_custom_separator():
    record = {"http": {"status": 404}}
    flat = flatten_record(record, separator="/")
    assert flat["http/status"] == 404


# ---------------------------------------------------------------------------
# extract_field
# ---------------------------------------------------------------------------

def test_extract_top_level_field():
    record = {"level": "error", "msg": "boom"}
    assert extract_field(record, "level") == "error"


def test_extract_nested_field():
    record = {"http": {"method": "POST", "status": 201}}
    assert extract_field(record, "http.status") == 201


def test_extract_missing_key_returns_none():
    record = {"level": "info"}
    assert extract_field(record, "missing") is None


def test_extract_missing_nested_key_returns_none():
    record = {"http": {"method": "GET"}}
    assert extract_field(record, "http.status") is None


def test_extract_list_index():
    record = {"tags": ["web", "api", "v2"]}
    assert extract_field(record, "tags.1") == "api"


def test_extract_list_out_of_range_returns_none():
    record = {"tags": ["web"]}
    assert extract_field(record, "tags.5") is None


# ---------------------------------------------------------------------------
# extract_fields
# ---------------------------------------------------------------------------

def test_extract_fields_multiple():
    record = {"level": "warn", "msg": "slow", "latency": 320}
    result = extract_fields(record, ["level", "latency"])
    assert result == {"level": "warn", "latency": 320}


def test_extract_fields_skips_missing():
    record = {"level": "info"}
    result = extract_fields(record, ["level", "nonexistent"])
    assert "nonexistent" not in result
    assert result["level"] == "info"


def test_extract_fields_empty_list():
    record = {"level": "debug"}
    assert extract_fields(record, []) == {}
