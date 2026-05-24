"""Tests for JsonPathFilter and its CLI."""
from __future__ import annotations

import json
import subprocess
import sys
from io import StringIO

import pytest

from logslice.json_path_filter import JsonPathFilter, JsonPathFilterError


# ---------------------------------------------------------------------------
# Construction guards
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(JsonPathFilterError, match="blank"):
        JsonPathFilter(field="", values=["prod"])


def test_blank_field_raises():
    with pytest.raises(JsonPathFilterError, match="blank"):
        JsonPathFilter(field="   ", values=["prod"])


def test_no_values_raises():
    with pytest.raises(JsonPathFilterError, match="at least one"):
        JsonPathFilter(field="env", values=[])


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_field_property():
    f = JsonPathFilter(field="meta.env", values=["prod"])
    assert f.field == "meta.env"


def test_values_stored_as_frozenset():
    f = JsonPathFilter(field="env", values=["prod", "staging"])
    assert f.values == frozenset({"prod", "staging"})


def test_invert_default_false():
    f = JsonPathFilter(field="env", values=["prod"])
    assert f.invert is False


# ---------------------------------------------------------------------------
# Matching – top-level field
# ---------------------------------------------------------------------------

def test_top_level_match_keeps_record():
    f = JsonPathFilter(field="env", values=["prod"])
    assert f.matches({"env": "prod"}) is True


def test_top_level_no_match_drops_record():
    f = JsonPathFilter(field="env", values=["prod"])
    assert f.matches({"env": "dev"}) is False


def test_nested_field_match():
    f = JsonPathFilter(field="meta.region", values=["us-east-1"])
    assert f.matches({"meta": {"region": "us-east-1"}}) is True


def test_nested_field_no_match():
    f = JsonPathFilter(field="meta.region", values=["us-east-1"])
    assert f.matches({"meta": {"region": "eu-west-1"}}) is False


# ---------------------------------------------------------------------------
# Invert
# ---------------------------------------------------------------------------

def test_invert_drops_matching_record():
    f = JsonPathFilter(field="env", values=["prod"], invert=True)
    assert f.matches({"env": "prod"}) is False


def test_invert_keeps_non_matching_record():
    f = JsonPathFilter(field="env", values=["prod"], invert=True)
    assert f.matches({"env": "dev"}) is True


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------

def test_case_insensitive_match():
    f = JsonPathFilter(field="env", values=["PROD"], case_sensitive=False)
    assert f.matches({"env": "prod"}) is True


def test_case_sensitive_no_match():
    f = JsonPathFilter(field="env", values=["PROD"], case_sensitive=True)
    assert f.matches({"env": "prod"}) is False


# ---------------------------------------------------------------------------
# Missing field
# ---------------------------------------------------------------------------

def test_missing_field_drops_by_default():
    f = JsonPathFilter(field="env", values=["prod"])
    assert f.matches({"other": "x"}) is False


def test_missing_field_kept_when_missing_ok():
    f = JsonPathFilter(field="env", values=["prod"], missing_ok=True)
    assert f.matches({"other": "x"}) is True


# ---------------------------------------------------------------------------
# filter() generator
# ---------------------------------------------------------------------------

def test_filter_yields_only_matching():
    f = JsonPathFilter(field="level", values=["error"])
    records = [
        {"level": "info"},
        {"level": "error"},
        {"level": "warn"},
        {"level": "error"},
    ]
    result = list(f.filter(records))
    assert result == [{"level": "error"}, {"level": "error"}]
