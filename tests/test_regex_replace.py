"""Unit tests for logslice.regex_replace."""

from __future__ import annotations

import pytest

from logslice.regex_replace import RegexReplace, RegexReplaceError


def test_empty_field_raises():
    with pytest.raises(RegexReplaceError, match="field"):
        RegexReplace(field="", pattern=r"\d+", replacement="X")


def test_blank_field_raises():
    with pytest.raises(RegexReplaceError, match="field"):
        RegexReplace(field="   ", pattern=r"\d+", replacement="X")


def test_empty_pattern_raises():
    with pytest.raises(RegexReplaceError, match="pattern"):
        RegexReplace(field="msg", pattern="", replacement="X")


def test_invalid_regex_raises():
    with pytest.raises(RegexReplaceError, match="invalid regex"):
        RegexReplace(field="msg", pattern="[unclosed", replacement="X")


def test_negative_count_raises():
    with pytest.raises(RegexReplaceError, match="count"):
        RegexReplace(field="msg", pattern=r"\d", replacement="X", count=-1)


def test_field_property():
    r = RegexReplace(field="message", pattern=r"\d+", replacement="N")
    assert r.field == "message"


def test_pattern_property():
    r = RegexReplace(field="msg", pattern=r"\d+", replacement="N")
    assert r.pattern == r"\d+"


def test_replacement_property():
    r = RegexReplace(field="msg", pattern=r"\d+", replacement="NUM")
    assert r.replacement == "NUM"


def test_count_property_default():
    r = RegexReplace(field="msg", pattern=r"\d+", replacement="N")
    assert r.count == 0


def test_simple_substitution():
    r = RegexReplace(field="msg", pattern=r"\d+", replacement="NUM")
    result = r.apply({"msg": "error 42 on line 7"})
    assert result["msg"] == "error NUM on line NUM"


def test_count_limits_substitutions():
    r = RegexReplace(field="msg", pattern=r"\d+", replacement="N", count=1)
    result = r.apply({"msg": "a1 b2 c3"})
    assert result["msg"] == "aN b2 c3"


def test_missing_field_returns_unchanged():
    r = RegexReplace(field="missing", pattern=r"\d+", replacement="N")
    record = {"msg": "hello"}
    result = r.apply(record)
    assert result == record


def test_non_string_field_returns_unchanged():
    r = RegexReplace(field="code", pattern=r"\d+", replacement="N")
    result = r.apply({"code": 404})
    assert result["code"] == 404


def test_does_not_mutate_original():
    r = RegexReplace(field="msg", pattern=r"foo", replacement="bar")
    original = {"msg": "foo baz"}
    r.apply(original)
    assert original["msg"] == "foo baz"


def test_nested_field_substitution():
    r = RegexReplace(field="meta.user", pattern=r"[aeiou]", replacement="*")
    result = r.apply({"meta": {"user": "alice"}})
    assert result["meta"]["user"] == "*l*c*"


def test_non_dict_record_raises():
    r = RegexReplace(field="msg", pattern=r"x", replacement="y")
    with pytest.raises(RegexReplaceError, match="dict"):
        r.apply(["not", "a", "dict"])  # type: ignore[arg-type]


def test_empty_replacement_deletes_matches():
    r = RegexReplace(field="msg", pattern=r"\s+", replacement="")
    result = r.apply({"msg": "hello world"})
    assert result["msg"] == "helloworld"
