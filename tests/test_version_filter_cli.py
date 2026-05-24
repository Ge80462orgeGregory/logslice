"""Tests for logslice.version_filter_cli."""
import io
import json
import pytest
from logslice.version_filter_cli import run_version_filter_cli


def _make_lines(*records):
    return io.StringIO("\n".join(json.dumps(r) for r in records) + "\n")


def _run(argv, lines):
    out = io.StringIO()
    rc = run_version_filter_cli(argv, stdin=lines, stdout=out)
    return rc, out.getvalue().strip().splitlines()


def test_missing_field_exits_2():
    rc, _ = _run(["--min", "1.0.0"], _make_lines({"v": "1.0.0"}))
    assert rc == 2


def test_no_bounds_exits_2():
    rc, _ = _run(["--field", "v"], _make_lines({"v": "1.0.0"}))
    assert rc == 2


def test_invalid_min_exits_2():
    rc, _ = _run(["--field", "v", "--min", "bad"], _make_lines({"v": "1.0.0"}))
    assert rc == 2


def test_min_keeps_matching():
    lines = _make_lines({"v": "1.0.0"}, {"v": "2.0.0"}, {"v": "0.9.0"})
    rc, output = _run(["--field", "v", "--min", "1.0.0"], lines)
    assert rc == 0
    assert len(output) == 2
    versions = [json.loads(l)["v"] for l in output]
    assert "1.0.0" in versions
    assert "2.0.0" in versions


def test_max_keeps_matching():
    lines = _make_lines({"v": "1.0.0"}, {"v": "2.0.0"}, {"v": "3.0.0"})
    rc, output = _run(["--field", "v", "--max", "2.0.0"], lines)
    assert rc == 0
    assert len(output) == 2


def test_range_filters_correctly():
    lines = _make_lines(
        {"v": "1.0.0"}, {"v": "1.5.0"}, {"v": "2.0.0"}, {"v": "2.5.0"}
    )
    rc, output = _run(["--field", "v", "--min", "1.5.0", "--max", "2.0.0"], lines)
    assert rc == 0
    assert len(output) == 2


def test_invert_flag():
    lines = _make_lines({"v": "1.0.0"}, {"v": "3.0.0"})
    rc, output = _run(["--field", "v", "--min", "2.0.0", "--invert"], lines)
    assert rc == 0
    assert len(output) == 1
    assert json.loads(output[0])["v"] == "1.0.0"


def test_invalid_json_lines_skipped():
    stdin = io.StringIO('not-json\n{"v": "1.0.0"}\n')
    rc, output = _run(["--field", "v", "--min", "1.0.0"], stdin)
    assert rc == 0
    assert len(output) == 1
