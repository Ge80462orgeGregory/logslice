"""Unit tests for logslice.pattern_filter."""

import pytest

from logslice.pattern_filter import PatternFilter, PatternFilterError


# ---------------------------------------------------------------------------
# Construction errors
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(PatternFilterError, match="field must be"):
        PatternFilter(field="", include=["foo"])


def test_no_patterns_raises():
    with pytest.raises(PatternFilterError, match="at least one"):
        PatternFilter(field="level")


def test_invalid_include_regex_raises():
    with pytest.raises(PatternFilterError, match="invalid regex"):
        PatternFilter(field="msg", include=["[unclosed"])


def test_invalid_exclude_regex_raises():
    with pytest.raises(PatternFilterError, match="invalid regex"):
        PatternFilter(field="msg", exclude=["*bad*"])


# ---------------------------------------------------------------------------
# Basic include / exclude
# ---------------------------------------------------------------------------

def test_include_match_returns_true():
    pf = PatternFilter(field="level", include=["ERROR"])
    assert pf.matches({"level": "ERROR", "msg": "boom"}) is True


def test_include_no_match_returns_false():
    pf = PatternFilter(field="level", include=["ERROR"])
    assert pf.matches({"level": "INFO", "msg": "ok"}) is False


def test_exclude_match_returns_false():
    pf = PatternFilter(field="level", exclude=["DEBUG"])
    assert pf.matches({"level": "DEBUG", "msg": "verbose"}) is False


def test_exclude_no_match_returns_true():
    pf = PatternFilter(field="level", exclude=["DEBUG"])
    assert pf.matches({"level": "INFO", "msg": "ok"}) is True


# ---------------------------------------------------------------------------
# Combined include + exclude
# ---------------------------------------------------------------------------

def test_include_and_exclude_both_match_exclude_wins():
    pf = PatternFilter(field="msg", include=["error"], exclude=["ignore"])
    assert pf.matches({"msg": "error ignore this"}) is False


def test_include_and_exclude_only_include_matches():
    pf = PatternFilter(field="msg", include=["error"], exclude=["ignore"])
    assert pf.matches({"msg": "critical error"}) is True


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------

def test_ignore_case_include():
    pf = PatternFilter(field="level", include=["error"], ignore_case=True)
    assert pf.matches({"level": "ERROR"}) is True


def test_ignore_case_exclude():
    pf = PatternFilter(field="level", exclude=["DEBUG"], ignore_case=True)
    assert pf.matches({"level": "debug"}) is False


# ---------------------------------------------------------------------------
# Missing / nested fields
# ---------------------------------------------------------------------------

def test_missing_field_with_include_returns_false():
    pf = PatternFilter(field="level", include=["ERROR"])
    assert pf.matches({"msg": "no level here"}) is False


def test_missing_field_with_only_exclude_returns_true():
    pf = PatternFilter(field="level", exclude=["DEBUG"])
    assert pf.matches({"msg": "no level key"}) is True


def test_nested_field_dot_notation():
    pf = PatternFilter(field="context.env", include=["prod"])
    assert pf.matches({"context": {"env": "production"}}) is True


def test_non_dict_record_raises():
    pf = PatternFilter(field="level", include=["ERROR"])
    with pytest.raises(PatternFilterError):
        pf.matches(["not", "a", "dict"])


# ---------------------------------------------------------------------------
# filter_records generator
# ---------------------------------------------------------------------------

def test_filter_records_yields_matching():
    pf = PatternFilter(field="level", include=["ERROR", "WARN"])
    records = [
        {"level": "INFO", "msg": "a"},
        {"level": "ERROR", "msg": "b"},
        {"level": "WARN", "msg": "c"},
        {"level": "DEBUG", "msg": "d"},
    ]
    result = list(pf.filter_records(records))
    assert len(result) == 2
    assert result[0]["msg"] == "b"
    assert result[1]["msg"] == "c"
