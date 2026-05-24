"""Tests for logslice.sequence_filter."""
import pytest

from logslice.sequence_filter import SequenceFilter, SequenceFilterError


def test_empty_field_raises():
    with pytest.raises(SequenceFilterError):
        SequenceFilter("")


def test_blank_field_raises():
    with pytest.raises(SequenceFilterError):
        SequenceFilter("   ")


def test_field_property():
    sf = SequenceFilter("seq")
    assert sf.field == "seq"


def test_decreasing_default_false():
    sf = SequenceFilter("n")
    assert sf.decreasing is False


def test_decreasing_stored():
    sf = SequenceFilter("n", decreasing=True)
    assert sf.decreasing is True


def test_last_value_none_initially():
    sf = SequenceFilter("n")
    assert sf.last_value is None


def test_first_record_always_passes():
    sf = SequenceFilter("n")
    assert sf.keep({"n": 5}) is True
    assert sf.last_value == 5.0


def test_increasing_passes():
    sf = SequenceFilter("n")
    sf.keep({"n": 1})
    assert sf.keep({"n": 2}) is True


def test_equal_value_dropped():
    sf = SequenceFilter("n")
    sf.keep({"n": 3})
    assert sf.keep({"n": 3}) is False


def test_decreasing_value_dropped():
    sf = SequenceFilter("n")
    sf.keep({"n": 10})
    assert sf.keep({"n": 5}) is False


def test_last_value_not_updated_on_drop():
    sf = SequenceFilter("n")
    sf.keep({"n": 10})
    sf.keep({"n": 5})
    assert sf.last_value == 10.0


def test_decreasing_mode_passes():
    sf = SequenceFilter("n", decreasing=True)
    sf.keep({"n": 100})
    assert sf.keep({"n": 50}) is True


def test_decreasing_mode_rejects_increase():
    sf = SequenceFilter("n", decreasing=True)
    sf.keep({"n": 100})
    assert sf.keep({"n": 200}) is False


def test_missing_field_dropped():
    sf = SequenceFilter("n")
    sf.keep({"n": 1})
    assert sf.keep({"other": 2}) is False


def test_non_numeric_field_dropped():
    sf = SequenceFilter("n")
    sf.keep({"n": 1})
    assert sf.keep({"n": "abc"}) is False


def test_non_dict_record_raises():
    sf = SequenceFilter("n")
    with pytest.raises(SequenceFilterError):
        sf.keep([1, 2, 3])  # type: ignore


def test_nested_field():
    sf = SequenceFilter("meta.seq")
    assert sf.keep({"meta": {"seq": 1}}) is True
    assert sf.keep({"meta": {"seq": 2}}) is True
    assert sf.keep({"meta": {"seq": 1}}) is False


def test_reset_clears_last_value():
    sf = SequenceFilter("n")
    sf.keep({"n": 50})
    sf.reset()
    assert sf.last_value is None
    assert sf.keep({"n": 1}) is True


def test_filter_returns_subset():
    sf = SequenceFilter("n")
    records = [{"n": i} for i in [3, 1, 4, 1, 5, 9, 2, 6]]
    result = sf.filter(records)
    values = [r["n"] for r in result]
    assert values == [3, 4, 5, 9]


def test_string_numeric_coerced():
    sf = SequenceFilter("n")
    assert sf.keep({"n": "1"}) is True
    assert sf.keep({"n": "2"}) is True
