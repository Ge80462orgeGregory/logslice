"""Tests for logslice.length_filter."""

import pytest

from logslice.length_filter import LengthFilter, LengthFilterError


def test_empty_field_raises():
    with pytest.raises(LengthFilterError, match="non-empty"):
        LengthFilter("", min_len=1)


def test_no_bounds_raises():
    with pytest.raises(LengthFilterError, match="at least one"):
        LengthFilter("msg")


def test_negative_min_raises():
    with pytest.raises(LengthFilterError, match=">= 0"):
        LengthFilter("msg", min_len=-1)


def test_negative_max_raises():
    with pytest.raises(LengthFilterError, match=">= 0"):
        LengthFilter("msg", max_len=-1)


def test_min_exceeds_max_raises():
    with pytest.raises(LengthFilterError, match="must not exceed"):
        LengthFilter("msg", min_len=10, max_len=5)


def test_field_property():
    f = LengthFilter("message", min_len=0)
    assert f.field == "message"


def test_min_len_property():
    f = LengthFilter("msg", min_len=3)
    assert f.min_len == 3
    assert f.max_len is None


def test_max_len_property():
    f = LengthFilter("msg", max_len=20)
    assert f.max_len == 20
    assert f.min_len is None


def test_matches_within_bounds():
    f = LengthFilter("msg", min_len=2, max_len=10)
    assert f.matches({"msg": "hello"}) is True


def test_matches_too_short():
    f = LengthFilter("msg", min_len=5)
    assert f.matches({"msg": "hi"}) is False


def test_matches_too_long():
    f = LengthFilter("msg", max_len=4)
    assert f.matches({"msg": "hello!"}) is False


def test_matches_exactly_min():
    f = LengthFilter("msg", min_len=3)
    assert f.matches({"msg": "abc"}) is True


def test_matches_exactly_max():
    f = LengthFilter("msg", max_len=5)
    assert f.matches({"msg": "hello"}) is True


def test_missing_field_returns_false():
    f = LengthFilter("msg", min_len=1)
    assert f.matches({"level": "info"}) is False


def test_non_string_field_returns_false():
    f = LengthFilter("count", min_len=1)
    assert f.matches({"count": 42}) is False


def test_nested_field():
    f = LengthFilter("meta.user", min_len=3, max_len=10)
    assert f.matches({"meta": {"user": "alice"}}) is True
    assert f.matches({"meta": {"user": "ab"}}) is False


def test_non_dict_record_raises():
    f = LengthFilter("msg", min_len=1)
    with pytest.raises(LengthFilterError, match="dict"):
        f.matches(["not", "a", "dict"])


def test_filter_records_yields_matching():
    f = LengthFilter("msg", min_len=4)
    records = [
        {"msg": "hi"},
        {"msg": "hello"},
        {"msg": "hey"},
        {"msg": "greetings"},
    ]
    result = list(f.filter_records(records))
    assert result == [{"msg": "hello"}, {"msg": "greetings"}]
