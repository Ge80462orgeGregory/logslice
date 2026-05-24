"""Tests for logslice.case_filter."""
import pytest
from logslice.case_filter import CaseFilter, CaseFilterError, VALID_STYLES


def test_empty_field_raises():
    with pytest.raises(CaseFilterError, match="field"):
        CaseFilter("", "upper")


def test_blank_field_raises():
    with pytest.raises(CaseFilterError, match="field"):
        CaseFilter("   ", "lower")


def test_invalid_style_raises():
    with pytest.raises(CaseFilterError, match="style"):
        CaseFilter("name", "pascal")


def test_valid_construction():
    f = CaseFilter("msg", "upper")
    assert f.field == "msg"
    assert f.style == "upper"
    assert f.invert is False


def test_invert_stored():
    f = CaseFilter("msg", "lower", invert=True)
    assert f.invert is True


def test_upper_matches():
    f = CaseFilter("level", "upper")
    assert f.matches({"level": "ERROR"}) is True


def test_upper_no_match():
    f = CaseFilter("level", "upper")
    assert f.matches({"level": "error"}) is False


def test_lower_matches():
    f = CaseFilter("env", "lower")
    assert f.matches({"env": "production"}) is True


def test_lower_no_match():
    f = CaseFilter("env", "lower")
    assert f.matches({"env": "Production"}) is False


def test_title_matches():
    f = CaseFilter("name", "title")
    assert f.matches({"name": "John Doe"}) is True


def test_title_no_match():
    f = CaseFilter("name", "title")
    assert f.matches({"name": "john doe"}) is False


def test_snake_matches():
    f = CaseFilter("key", "snake")
    assert f.matches({"key": "my_field_name"}) is True


def test_snake_no_match():
    f = CaseFilter("key", "snake")
    assert f.matches({"key": "myFieldName"}) is False


def test_camel_matches():
    f = CaseFilter("key", "camel")
    assert f.matches({"key": "myFieldName"}) is True


def test_camel_no_match():
    f = CaseFilter("key", "camel")
    assert f.matches({"key": "my_field_name"}) is False


def test_invert_flips_result():
    f = CaseFilter("level", "upper", invert=True)
    assert f.matches({"level": "ERROR"}) is False
    assert f.matches({"level": "error"}) is True


def test_missing_field_returns_false():
    f = CaseFilter("level", "upper")
    assert f.matches({"msg": "hello"}) is False


def test_non_string_field_returns_false():
    f = CaseFilter("count", "upper")
    assert f.matches({"count": 42}) is False


def test_nested_field():
    f = CaseFilter("meta.env", "upper")
    assert f.matches({"meta": {"env": "PROD"}}) is True
    assert f.matches({"meta": {"env": "prod"}}) is False


def test_non_dict_record_raises():
    f = CaseFilter("level", "lower")
    with pytest.raises(CaseFilterError, match="dict"):
        f.matches(["not", "a", "dict"])


def test_all_valid_styles_accepted():
    for style in VALID_STYLES:
        f = CaseFilter("field", style)
        assert f.style == style
