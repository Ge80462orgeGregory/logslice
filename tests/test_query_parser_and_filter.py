"""Tests for query_parser and filter_engine modules."""

import json
import pytest

from logslice.query_parser import parse_query, evaluate, QueryParseError, QueryExpression
from logslice.filter_engine import FilterEngine


# ---------------------------------------------------------------------------
# parse_query tests
# ---------------------------------------------------------------------------

def test_parse_equals():
    expr = parse_query("level=error")
    assert expr.field == "level"
    assert expr.operator == "="
    assert expr.value == "error"


def test_parse_gte_numeric():
    expr = parse_query("status>=400")
    assert expr.operator == ">="
    assert expr.value == 400


def test_parse_contains():
    expr = parse_query("message~timeout")
    assert expr.operator == "~"
    assert expr.value == "timeout"


def test_parse_nested_field():
    expr = parse_query("http.status=200")
    assert expr.field == "http.status"


def test_parse_no_operator_raises():
    with pytest.raises(QueryParseError):
        parse_query("levelERROR")


def test_parse_missing_value_raises():
    with pytest.raises(QueryParseError):
        parse_query("level=")


# ---------------------------------------------------------------------------
# evaluate tests
# ---------------------------------------------------------------------------

def test_evaluate_equals_match():
    expr = QueryExpression(field="level", operator="=", value="error")
    assert evaluate({"level": "ERROR"}, expr) is True


def test_evaluate_gt_match():
    expr = QueryExpression(field="status", operator=">", value=399)
    assert evaluate({"status": 404}, expr) is True


def test_evaluate_missing_field_returns_false():
    expr = QueryExpression(field="missing", operator="=", value="x")
    assert evaluate({"level": "info"}, expr) is False


def test_evaluate_nested_field():
    expr = QueryExpression(field="http.status", operator="=", value=200)
    assert evaluate({"http": {"status": 200}}, expr) is True


def test_evaluate_regex_match():
    expr = QueryExpression(field="message", operator="~", value="time.?out")
    assert evaluate({"message": "Connection timed out"}, expr) is True


# ---------------------------------------------------------------------------
# FilterEngine tests
# ---------------------------------------------------------------------------

def _make_lines(*entries):
    return [json.dumps(e) for e in entries]


def test_filter_engine_single_query():
    engine = FilterEngine(["level=error"])
    lines = _make_lines(
        {"level": "info", "msg": "ok"},
        {"level": "error", "msg": "boom"},
    )
    results = list(engine.filter_lines(lines))
    assert len(results) == 1
    assert results[0]["msg"] == "boom"


def test_filter_engine_multiple_queries():
    engine = FilterEngine(["level=error", "status>=500"])
    lines = _make_lines(
        {"level": "error", "status": 404},
        {"level": "error", "status": 503},
        {"level": "info", "status": 503},
    )
    results = list(engine.filter_lines(lines))
    assert len(results) == 1
    assert results[0]["status"] == 503


def test_filter_engine_skips_invalid_json():
    engine = FilterEngine()
    lines = ["not json", "{\"level\": \"info\"}", ""]
    results = list(engine.filter_lines(lines))
    assert len(results) == 1
