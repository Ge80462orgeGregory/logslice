"""Tests for logslice.suffix_filter."""

import pytest

from logslice.suffix_filter import SuffixFilter, SuffixFilterError


def test_empty_field_raises():
    with pytest.raises(SuffixFilterError, match="field"):
        SuffixFilter("", "error")


def test_blank_field_raises():
    with pytest.raises(SuffixFilterError, match="field"):
        SuffixFilter("   ", "error")


def test_none_suffix_raises():
    with pytest.raises(SuffixFilterError, match="suffix"):
        SuffixFilter("msg", None)  # type: ignore[arg-type]


def test_field_property():
    f = SuffixFilter("  level  ", ".err")
    assert f.field == "level"


def test_suffix_property():
    f = SuffixFilter("msg", ".ERROR")
    assert f.suffix == ".ERROR"


def test_case_insensitive_default():
    f = SuffixFilter("msg", ".log")
    assert f.case_sensitive is False


def test_invert_default_false():
    f = SuffixFilter("msg", ".log")
    assert f.invert is False


def test_basic_suffix_match():
    f = SuffixFilter("msg", ".log")
    assert f.matches({"msg": "access.log"}) is True


def test_basic_suffix_no_match():
    f = SuffixFilter("msg", ".log")
    assert f.matches({"msg": "access.txt"}) is False


def test_case_insensitive_match():
    f = SuffixFilter("msg", ".LOG")
    assert f.matches({"msg": "access.log"}) is True


def test_case_sensitive_no_match():
    f = SuffixFilter("msg", ".LOG", case_sensitive=True)
    assert f.matches({"msg": "access.log"}) is False


def test_case_sensitive_match():
    f = SuffixFilter("msg", ".LOG", case_sensitive=True)
    assert f.matches({"msg": "access.LOG"}) is True


def test_invert_keeps_non_matching():
    f = SuffixFilter("msg", ".log", invert=True)
    assert f.matches({"msg": "access.txt"}) is True


def test_invert_drops_matching():
    f = SuffixFilter("msg", ".log", invert=True)
    assert f.matches({"msg": "access.log"}) is False


def test_missing_field_returns_false():
    f = SuffixFilter("msg", ".log")
    assert f.matches({"level": "info"}) is False


def test_non_string_field_returns_false():
    f = SuffixFilter("code", "42")
    assert f.matches({"code": 42}) is False


def test_nested_field_match():
    f = SuffixFilter("request.path", "/api")
    assert f.matches({"request": {"path": "/v1/api"}}) is True


def test_nested_field_no_match():
    f = SuffixFilter("request.path", "/api")
    assert f.matches({"request": {"path": "/v1/data"}}) is False


def test_non_dict_record_raises():
    f = SuffixFilter("msg", ".log")
    with pytest.raises(SuffixFilterError, match="dict"):
        f.matches("not a dict")  # type: ignore[arg-type]


def test_empty_suffix_matches_any_string():
    f = SuffixFilter("msg", "")
    assert f.matches({"msg": "anything"}) is True
