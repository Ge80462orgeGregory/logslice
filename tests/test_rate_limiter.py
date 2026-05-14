"""Tests for logslice.rate_limiter."""

import time
import pytest

from logslice.rate_limiter import RateLimiter, RateLimitExceeded


def test_invalid_max_raises():
    with pytest.raises(ValueError):
        RateLimiter(0)


def test_allow_within_limit():
    rl = RateLimiter(max_lines_per_second=5)
    for _ in range(5):
        assert rl.allow() is True


def test_allow_exceeds_limit():
    rl = RateLimiter(max_lines_per_second=3)
    for _ in range(3):
        rl.allow()
    assert rl.allow() is False


def test_check_raises_on_exceeded():
    rl = RateLimiter(max_lines_per_second=2)
    rl.check()
    rl.check()
    with pytest.raises(RateLimitExceeded):
        rl.check()


def test_check_does_not_raise_within_limit():
    rl = RateLimiter(max_lines_per_second=10)
    for _ in range(10):
        rl.check()  # should not raise


def test_window_expires_allows_new_lines():
    rl = RateLimiter(max_lines_per_second=2, window_seconds=0.1)
    rl.allow()
    rl.allow()
    assert rl.allow() is False
    time.sleep(0.15)
    assert rl.allow() is True


def test_current_count_reflects_window():
    rl = RateLimiter(max_lines_per_second=10, window_seconds=0.1)
    rl.allow()
    rl.allow()
    assert rl.current_count == 2
    time.sleep(0.15)
    assert rl.current_count == 0


def test_reset_clears_state():
    rl = RateLimiter(max_lines_per_second=2)
    rl.allow()
    rl.allow()
    assert rl.allow() is False
    rl.reset()
    assert rl.allow() is True


def test_allow_returns_bool():
    rl = RateLimiter(max_lines_per_second=5)
    result = rl.allow()
    assert isinstance(result, bool)
