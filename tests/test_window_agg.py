"""Tests for logslice.window_agg and logslice.window_agg_cli."""
from __future__ import annotations

import json
import io
import pytest

from logslice.window_agg import WindowAgg, WindowAggError
from logslice.window_agg_cli import build_window_agg_parser, run_window_agg_cli


# ---------------------------------------------------------------------------
# WindowAgg unit tests
# ---------------------------------------------------------------------------

def test_empty_field_raises():
    with pytest.raises(WindowAggError, match="field"):
        WindowAgg(field="", window=10, stats=["count"])


def test_zero_window_raises():
    with pytest.raises(WindowAggError, match="window"):
        WindowAgg(field="latency", window=0, stats=["count"])


def test_negative_window_raises():
    with pytest.raises(WindowAggError, match="window"):
        WindowAgg(field="latency", window=-5, stats=["count"])


def test_no_stats_raises():
    with pytest.raises(WindowAggError, match="at least one"):
        WindowAgg(field="latency", window=10, stats=[])


def test_unknown_stat_raises():
    with pytest.raises(WindowAggError, match="unknown stats"):
        WindowAgg(field="latency", window=10, stats=["median"])


def test_field_and_window_stored():
    agg = WindowAgg(field="latency", window=10, stats=["count"])
    assert agg.field == "latency"
    assert agg.window == 10


def test_feed_non_dict_raises():
    agg = WindowAgg(field="v", window=5, stats=["count"])
    with pytest.raises(WindowAggError):
        agg.feed([1, 2, 3])


def test_missing_field_increments_skipped():
    agg = WindowAgg(field="v", window=5, stats=["count"])
    agg.feed({"other": 1})
    assert agg.skipped == 1


def test_non_numeric_field_increments_skipped():
    agg = WindowAgg(field="v", window=5, stats=["count"])
    agg.feed({"v": "hello"})
    assert agg.skipped == 1


def test_single_record_counted():
    agg = WindowAgg(field="v", window=10, stats=["count"])
    agg.feed({"v": 5})
    results = agg.results()
    assert len(results) == 1
    bucket_start, stats = results[0]
    assert bucket_start == 0
    assert stats["count"] == 1.0


def test_two_records_same_bucket():
    agg = WindowAgg(field="v", window=10, stats=["count", "sum"])
    agg.feed({"v": 3})
    agg.feed({"v": 7})
    results = agg.results()
    assert len(results) == 1
    _, stats = results[0]
    assert stats["count"] == 2.0
    assert stats["sum"] == 10.0


def test_two_records_different_buckets():
    agg = WindowAgg(field="v", window=10, stats=["count"])
    agg.feed({"v": 5})
    agg.feed({"v": 15})
    results = agg.results()
    assert len(results) == 2
    assert results[0][0] == 0
    assert results[1][0] == 10


def test_min_max_mean_computed():
    agg = WindowAgg(field="v", window=100, stats=["min", "max", "mean"])
    for v in [10, 20, 30]:
        agg.feed({"v": v})
    _, stats = agg.results()[0]
    assert stats["min"] == 10
    assert stats["max"] == 30
    assert abs(stats["mean"] - 20.0) < 1e-9


def test_nested_field_resolved():
    agg = WindowAgg(field="metrics.latency", window=10, stats=["count"])
    agg.feed({"metrics": {"latency": 5}})
    results = agg.results()
    assert results[0][1]["count"] == 1.0


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _make_lines(records):
    return [json.dumps(r) + "\n" for r in records]


def _run(argv, records):
    parser = build_window_agg_parser()
    args = parser.parse_args(argv)
    out, err = io.StringIO(), io.StringIO()
    code = run_window_agg_cli(args, _make_lines(records), out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_cli_missing_field_exits_2():
    parser = build_window_agg_parser()
    args = parser.parse_args(["--field", "", "--window", "10"])
    out, err = io.StringIO(), io.StringIO()
    code = run_window_agg_cli(args, [], out=out, err=err)
    assert code == 2


def test_cli_basic_output():
    records = [{"v": i} for i in range(5)]
    code, out, _ = _run(["--field", "v", "--window", "10", "--stats", "count", "sum"], records)
    assert code == 0
    rows = [json.loads(line) for line in out.strip().splitlines()]
    assert len(rows) == 1
    assert rows[0]["count"] == 5.0
    assert rows[0]["bucket_start"] == 0
    assert rows[0]["bucket_end"] == 10


def test_cli_invalid_json_skipped():
    lines = ["not-json\n", json.dumps({"v": 5}) + "\n"]
    parser = build_window_agg_parser()
    args = parser.parse_args(["--field", "v", "--window", "10", "--stats", "count"])
    out, err = io.StringIO(), io.StringIO()
    code = run_window_agg_cli(args, lines, out=out, err=err)
    assert code == 0
    rows = [json.loads(l) for l in out.strip().splitlines()]
    assert rows[0]["count"] == 1.0
