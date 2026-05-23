"""Tests for logslice.top_values.TopValues."""

import pytest

from logslice.top_values import TopValues, TopValuesError


def test_empty_field_raises():
    with pytest.raises(TopValuesError, match="non-empty"):
        TopValues(field="")


def test_n_less_than_one_raises():
    with pytest.raises(TopValuesError, match="n must be"):
        TopValues(field="status", n=0)


def test_feed_non_dict_raises():
    tv = TopValues(field="status")
    with pytest.raises(TopValuesError, match="dict"):
        tv.feed("not a dict")


def test_single_record_counted():
    tv = TopValues(field="status")
    tv.feed({"status": "200"})
    assert tv.total == 1
    assert tv.top() == [("200", 1)]


def test_top_n_limits_results():
    tv = TopValues(field="code", n=2)
    records = [
        {"code": "A"}, {"code": "A"}, {"code": "A"},
        {"code": "B"}, {"code": "B"},
        {"code": "C"},
    ]
    tv.feed_many(records)
    top = tv.top()
    assert len(top) == 2
    assert top[0] == ("A", 3)
    assert top[1] == ("B", 2)


def test_missing_field_tracked():
    tv = TopValues(field="level")
    tv.feed({"level": "info"})
    tv.feed({"msg": "no level here"})
    assert tv.missing == 1
    assert tv.total == 2


def test_nested_field_dot_notation():
    tv = TopValues(field="http.status")
    tv.feed({"http": {"status": "404"}})
    tv.feed({"http": {"status": "404"}})
    tv.feed({"http": {"status": "200"}})
    top = tv.top()
    assert top[0] == ("404", 2)
    assert top[1] == ("200", 1)


def test_nested_field_missing_intermediate():
    tv = TopValues(field="http.status")
    tv.feed({"other": "value"})
    assert tv.missing == 1


def test_values_coerced_to_string():
    tv = TopValues(field="code")
    tv.feed({"code": 200})
    tv.feed({"code": 200})
    top = tv.top()
    assert top[0] == ("200", 2)


def test_summary_structure():
    tv = TopValues(field="env", n=3)
    tv.feed({"env": "prod"})
    tv.feed({"env": "dev"})
    tv.feed({"env": "prod"})
    s = tv.summary()
    assert s["field"] == "env"
    assert s["n"] == 3
    assert s["total"] == 3
    assert s["missing"] == 0
    assert s["top"][0] == {"value": "prod", "count": 2}
    assert s["top"][1] == {"value": "dev", "count": 1}


def test_feed_many_counts_correctly():
    tv = TopValues(field="region")
    tv.feed_many([
        {"region": "us-east"},
        {"region": "eu-west"},
        {"region": "us-east"},
    ])
    assert tv.total == 3
    assert tv.top()[0] == ("us-east", 2)
