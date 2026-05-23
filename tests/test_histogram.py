"""Tests for logslice.histogram."""

import pytest

from logslice.histogram import Histogram, HistogramError


def test_empty_field_raises():
    with pytest.raises(HistogramError, match="field"):
        Histogram(field="", bucket_size=1.0)


def test_zero_bucket_size_raises():
    with pytest.raises(HistogramError, match="bucket_size"):
        Histogram(field="latency", bucket_size=0)


def test_negative_bucket_size_raises():
    with pytest.raises(HistogramError, match="bucket_size"):
        Histogram(field="latency", bucket_size=-5.0)


def test_feed_non_dict_raises():
    h = Histogram("x", 1.0)
    with pytest.raises(HistogramError, match="dict"):
        h.feed([1, 2, 3])  # type: ignore[arg-type]


def test_single_record_counted():
    h = Histogram("latency", bucket_size=10.0)
    h.feed({"latency": 25.0})
    assert h.total == 1
    assert h.skipped == 0


def test_missing_field_skipped():
    h = Histogram("latency", bucket_size=10.0)
    h.feed({"other": 5})
    assert h.skipped == 1
    assert h.total == 0


def test_non_numeric_field_skipped():
    h = Histogram("latency", bucket_size=10.0)
    h.feed({"latency": "fast"})
    assert h.skipped == 1


def test_bucket_boundaries():
    h = Histogram("v", bucket_size=10.0)
    h.feed_many([{"v": 0}, {"v": 9}, {"v": 10}, {"v": 19}])
    buckets = h.buckets()
    assert len(buckets) == 2
    assert buckets[0] == (0.0, 10.0, 2)
    assert buckets[1] == (10.0, 20.0, 2)


def test_feed_many_totals():
    h = Histogram("score", bucket_size=5.0)
    records = [{"score": i} for i in range(20)]
    h.feed_many(records)
    assert h.total == 20
    assert sum(c for _, _, c in h.buckets()) == 20


def test_nested_field():
    h = Histogram("http.duration_ms", bucket_size=100.0)
    h.feed({"http": {"duration_ms": 250}})
    assert h.total == 1
    buckets = h.buckets()
    assert buckets[0][0] == 200.0


def test_render_no_data():
    h = Histogram("x", 1.0)
    assert h.render() == "(no data)"


def test_render_produces_lines():
    h = Histogram("x", 10.0)
    h.feed_many([{"x": 5}, {"x": 15}, {"x": 25}])
    output = h.render(bar_width=20)
    lines = output.strip().splitlines()
    assert len(lines) == 3
    assert "#" in output


def test_render_max_bar_for_highest_bucket():
    h = Histogram("x", 10.0)
    h.feed_many([{"x": 1}] * 10 + [{"x": 11}] * 5)
    output = h.render(bar_width=10)
    first_line = output.splitlines()[0]
    assert "##########" in first_line
