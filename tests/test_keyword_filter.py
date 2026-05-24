"""Tests for logslice.keyword_filter."""

import pytest

from logslice.keyword_filter import KeywordFilter, KeywordFilterError


# ---------------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(KeywordFilterError, match="field"):
        KeywordFilter("", ["error"])


def test_blank_field_raises():
    with pytest.raises(KeywordFilterError, match="field"):
        KeywordFilter("   ", ["error"])


def test_no_keywords_raises():
    with pytest.raises(KeywordFilterError, match="keyword"):
        KeywordFilter("message", [])


def test_non_string_keyword_raises():
    with pytest.raises(KeywordFilterError, match="strings"):
        KeywordFilter("message", ["ok", 42])  # type: ignore[list-item]


def test_valid_construction():
    kf = KeywordFilter("message", ["error", "warn"])
    assert kf.field == "message"
    assert kf.keywords == ["error", "warn"]
    assert kf.match_any is True
    assert kf.case_sensitive is False
    assert kf.invert is False


# ---------------------------------------------------------------------------
# Basic matching — case-insensitive (default)
# ---------------------------------------------------------------------------

def test_single_keyword_match():
    kf = KeywordFilter("msg", ["error"])
    assert kf.matches({"msg": "An ERROR occurred"}) is True


def test_single_keyword_no_match():
    kf = KeywordFilter("msg", ["error"])
    assert kf.matches({"msg": "everything is fine"}) is False


def test_match_any_true_first_keyword():
    kf = KeywordFilter("msg", ["error", "warn"], match_any=True)
    assert kf.matches({"msg": "a warning issued"}) is True


def test_match_any_false_requires_all():
    kf = KeywordFilter("msg", ["error", "warn"], match_any=False)
    assert kf.matches({"msg": "error and warn present"}) is True
    assert kf.matches({"msg": "only error here"}) is False


# ---------------------------------------------------------------------------
# Case sensitivity
# ---------------------------------------------------------------------------

def test_case_sensitive_no_match_wrong_case():
    kf = KeywordFilter("msg", ["ERROR"], case_sensitive=True)
    assert kf.matches({"msg": "an error occurred"}) is False


def test_case_sensitive_match_correct_case():
    kf = KeywordFilter("msg", ["ERROR"], case_sensitive=True)
    assert kf.matches({"msg": "an ERROR occurred"}) is True


# ---------------------------------------------------------------------------
# Invert
# ---------------------------------------------------------------------------

def test_invert_drops_matching_record():
    kf = KeywordFilter("msg", ["error"], invert=True)
    assert kf.matches({"msg": "critical error"}) is False


def test_invert_keeps_non_matching_record():
    kf = KeywordFilter("msg", ["error"], invert=True)
    assert kf.matches({"msg": "all good"}) is True


# ---------------------------------------------------------------------------
# Nested field
# ---------------------------------------------------------------------------

def test_nested_field_match():
    kf = KeywordFilter("context.message", ["timeout"])
    record = {"context": {"message": "connection timeout reached"}}
    assert kf.matches(record) is True


def test_nested_field_missing_returns_false():
    kf = KeywordFilter("context.message", ["timeout"])
    assert kf.matches({"context": {}}) is False


def test_top_level_field_missing_returns_false():
    kf = KeywordFilter("msg", ["error"])
    assert kf.matches({"level": "info"}) is False


# ---------------------------------------------------------------------------
# Non-dict record raises
# ---------------------------------------------------------------------------

def test_non_dict_record_raises():
    kf = KeywordFilter("msg", ["error"])
    with pytest.raises(KeywordFilterError, match="dict"):
        kf.matches("not a dict")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Numeric field coerced to string
# ---------------------------------------------------------------------------

def test_numeric_field_coerced_to_string():
    kf = KeywordFilter("code", ["404"])
    assert kf.matches({"code": 404}) is True
