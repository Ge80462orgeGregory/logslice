"""Tests for logslice.count_filter."""
from __future__ import annotations

import pytest

from logslice.count_filter import CountFilter, CountFilterError


def test_empty_field_raises():
    with pytest.raises(CountFilterError, match="non-empty"):
        CountFilter(field="", min_count=1)


def test_blank_field_raises():
    with pytest.raises(CountFilterError, match="non-empty"):
        CountFilter(field="   ", min_count=1)


def test_no_bounds_raises():
    with pytest.raises(CountFilterError, match="at least one"):
        CountFilter(field="level")


def test_min_less_than_one_raises():
    with pytest.raises(CountFilterError, match="min_count must be >= 1"):
        CountFilter(field="level", min_count=0)


def test_max_less_than_one_raises():
    with pytest.raises(CountFilterError, match="max_count must be >= 1"):
        CountFilter(field="level", max_count=0)


def test_min_exceeds_max_raises():
    with pytest.raises(CountFilterError, match="must not exceed"):
        CountFilter(field="level", min_count=5, max_count=3)


def test_field_property():
    cf = CountFilter(field="level", min_count=1)
    assert cf.field == "level"


def test_min_max_properties():
    cf = CountFilter(field="level", min_count=2, max_count=4)
    assert cf.min_count == 2
    assert cf.max_count == 4


def test_invert_default_false():
    cf = CountFilter(field="level", min_count=1)
    assert cf.invert is False


def test_first_occurrence_excluded_when_min_is_2():
    cf = CountFilter(field="level", min_count=2)
    record = {"level": "error"}
    assert cf.matches(record) is False


def test_second_occurrence_included_when_min_is_2():
    cf = CountFilter(field="level", min_count=2)
    record = {"level": "error"}
    cf.matches(record)
    assert cf.matches(record) is True


def test_max_count_drops_after_threshold():
    cf = CountFilter(field="level", max_count=2)
    record = {"level": "warn"}
    assert cf.matches(record) is True   # count=1
    assert cf.matches(record) is True   # count=2
    assert cf.matches(record) is False  # count=3


def test_invert_flips_result():
    cf = CountFilter(field="level", max_count=1, invert=True)
    record = {"level": "info"}
    assert cf.matches(record) is False  # count=1, in_range=True → inverted=False
    assert cf.matches(record) is True   # count=2, in_range=False → inverted=True


def test_nested_field_tracked():
    cf = CountFilter(field="http.status", min_count=2)
    r = {"http": {"status": 200}}
    cf.matches(r)
    assert cf.matches(r) is True


def test_missing_field_value_counted_as_none():
    cf = CountFilter(field="missing", min_count=2)
    r = {"level": "info"}
    cf.matches(r)
    assert cf.matches(r) is True


def test_seen_counts_reflects_all_calls():
    cf = CountFilter(field="level", min_count=1)
    for _ in range(3):
        cf.matches({"level": "debug"})
    assert cf.seen_counts()["debug"] == 3


def test_filter_generator_yields_matching():
    cf = CountFilter(field="level", min_count=2, max_count=3)
    records = [{"level": "error"}] * 5
    results = list(cf.filter(iter(records)))
    assert len(results) == 2


def test_non_dict_raises():
    cf = CountFilter(field="level", min_count=1)
    with pytest.raises(CountFilterError, match="dict"):
        cf.matches("not a dict")  # type: ignore
