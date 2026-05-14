"""Tests for logslice.output_throttle."""

import json
import pytest

from logslice.output_formatter import OutputFormatter
from logslice.rate_limiter import RateLimiter
from logslice.output_throttle import OutputThrottle

VALID_LINE = json.dumps({"level": "info", "msg": "hello"})
INVALID_LINE = "not json at all"


def make_throttle(max_lps: int = 5) -> OutputThrottle:
    formatter = OutputFormatter(fmt="compact")
    limiter = RateLimiter(max_lines_per_second=max_lps)
    return OutputThrottle(formatter=formatter, rate_limiter=limiter)


def test_emit_returns_formatted_string():
    throttle = make_throttle(max_lps=10)
    result = throttle.emit(VALID_LINE)
    assert result is not None
    assert "hello" in result


def test_emitted_counter_increments():
    throttle = make_throttle(max_lps=10)
    throttle.emit(VALID_LINE)
    throttle.emit(VALID_LINE)
    assert throttle.emitted == 2


def test_dropped_counter_increments_on_rate_exceeded():
    throttle = make_throttle(max_lps=2)
    throttle.emit(VALID_LINE)
    throttle.emit(VALID_LINE)
    result = throttle.emit(VALID_LINE)  # should be dropped
    assert result is None
    assert throttle.dropped == 1


def test_no_rate_limiter_always_emits():
    formatter = OutputFormatter(fmt="compact")
    throttle = OutputThrottle(formatter=formatter, rate_limiter=None)
    for _ in range(100):
        assert throttle.emit(VALID_LINE) is not None
    assert throttle.dropped == 0


def test_invalid_json_returns_none_not_counted():
    throttle = make_throttle(max_lps=10)
    result = throttle.emit(INVALID_LINE)
    # OutputFormatter returns None for invalid JSON in compact/pretty modes
    assert result is None
    assert throttle.emitted == 0


def test_reset_counters():
    throttle = make_throttle(max_lps=1)
    throttle.emit(VALID_LINE)
    throttle.emit(VALID_LINE)  # dropped
    assert throttle.emitted == 1
    assert throttle.dropped == 1
    throttle.reset_counters()
    assert throttle.emitted == 0
    assert throttle.dropped == 0


def test_emit_total_equals_emitted_plus_dropped():
    throttle = make_throttle(max_lps=3)
    total = 6
    for _ in range(total):
        throttle.emit(VALID_LINE)
    assert throttle.emitted + throttle.dropped == total
