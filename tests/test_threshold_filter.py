"""Tests for logslice.threshold_filter."""

import pytest

from logslice.threshold_filter import ThresholdFilter, ThresholdFilterError


def test_empty_field_raises():
    with pytest.raises(ThresholdFilterError):
        ThresholdFilter(field="", threshold=10)


def test_blank_field_raises():
    with pytest.raises(ThresholdFilterError):
        ThresholdFilter(field="   ", threshold=10)


def test_invalid_direction_raises():
    with pytest.raises(ThresholdFilterError, match="direction"):
        ThresholdFilter(field="val", threshold=5, direction="sideways")


def test_field_property():
    f = ThresholdFilter(field="  score  ", threshold=50)
    assert f.field == "score"


def test_threshold_property():
    f = ThresholdFilter(field="score", threshold=42)
    assert f.threshold == 42.0


def test_direction_defaults_to_above():
    f = ThresholdFilter(field="score", threshold=10)
    assert f.direction == "above"


def test_inclusive_defaults_to_true():
    f = ThresholdFilter(field="score", threshold=10)
    assert f.inclusive is True


def test_invert_defaults_to_false():
    f = ThresholdFilter(field="score", threshold=10)
    assert f.invert is False


def test_above_inclusive_passes_equal():
    f = ThresholdFilter(field="v", threshold=10, direction="above", inclusive=True)
    assert f.matches({"v": 10}) is True


def test_above_inclusive_passes_greater():
    f = ThresholdFilter(field="v", threshold=10, direction="above", inclusive=True)
    assert f.matches({"v": 11}) is True


def test_above_inclusive_drops_less():
    f = ThresholdFilter(field="v", threshold=10, direction="above", inclusive=True)
    assert f.matches({"v": 9}) is False


def test_above_exclusive_drops_equal():
    f = ThresholdFilter(field="v", threshold=10, direction="above", inclusive=False)
    assert f.matches({"v": 10}) is False


def test_below_inclusive_passes_equal():
    f = ThresholdFilter(field="v", threshold=5, direction="below", inclusive=True)
    assert f.matches({"v": 5}) is True


def test_below_exclusive_drops_equal():
    f = ThresholdFilter(field="v", threshold=5, direction="below", inclusive=False)
    assert f.matches({"v": 5}) is False


def test_equal_direction_exact_match():
    f = ThresholdFilter(field="v", threshold=7, direction="equal")
    assert f.matches({"v": 7}) is True


def test_equal_direction_no_match():
    f = ThresholdFilter(field="v", threshold=7, direction="equal")
    assert f.matches({"v": 8}) is False


def test_invert_flips_result():
    f = ThresholdFilter(field="v", threshold=10, direction="above", invert=True)
    assert f.matches({"v": 15}) is False
    assert f.matches({"v": 5}) is True


def test_missing_field_returns_false():
    f = ThresholdFilter(field="missing", threshold=10)
    assert f.matches({"other": 20}) is False


def test_non_numeric_field_returns_false():
    f = ThresholdFilter(field="v", threshold=10)
    assert f.matches({"v": "high"}) is False


def test_nested_field_supported():
    f = ThresholdFilter(field="metrics.latency", threshold=100, direction="below")
    assert f.matches({"metrics": {"latency": 80}}) is True
    assert f.matches({"metrics": {"latency": 120}}) is False


def test_non_dict_record_raises():
    f = ThresholdFilter(field="v", threshold=1)
    with pytest.raises(ThresholdFilterError):
        f.matches([1, 2, 3])  # type: ignore[arg-type]


def test_string_numeric_value_coerced():
    f = ThresholdFilter(field="v", threshold=10, direction="above")
    assert f.matches({"v": "15"}) is True
