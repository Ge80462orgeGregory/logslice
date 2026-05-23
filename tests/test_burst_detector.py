"""Tests for logslice.burst_detector."""

from __future__ import annotations

import pytest

from logslice.burst_detector import BurstDetector, BurstDetectorError


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_invalid_threshold_raises():
    with pytest.raises(BurstDetectorError, match="threshold"):
        BurstDetector(threshold=0, window_seconds=1.0)


def test_invalid_window_raises():
    with pytest.raises(BurstDetectorError, match="window_seconds"):
        BurstDetector(threshold=5, window_seconds=0)


def test_negative_window_raises():
    with pytest.raises(BurstDetectorError, match="window_seconds"):
        BurstDetector(threshold=5, window_seconds=-1.0)


# ---------------------------------------------------------------------------
# Basic recording
# ---------------------------------------------------------------------------

def test_no_burst_below_threshold():
    d = BurstDetector(threshold=3, window_seconds=10.0)
    for i in range(3):
        assert d.record(ts=float(i)) is False


def test_burst_on_threshold_exceeded():
    d = BurstDetector(threshold=3, window_seconds=10.0)
    for i in range(3):
        d.record(ts=float(i))
    result = d.record(ts=3.0)
    assert result is True


def test_burst_count_increments():
    d = BurstDetector(threshold=2, window_seconds=10.0)
    d.record(ts=0.0)
    d.record(ts=1.0)
    d.record(ts=2.0)  # burst
    d.record(ts=3.0)  # burst
    assert d.burst_count == 2


# ---------------------------------------------------------------------------
# Sliding window eviction
# ---------------------------------------------------------------------------

def test_old_events_evicted_from_window():
    d = BurstDetector(threshold=3, window_seconds=5.0)
    d.record(ts=0.0)
    d.record(ts=1.0)
    d.record(ts=2.0)
    # Advance time past the window so all earlier events are evicted
    assert d.current_window_count(ts=10.0) == 0


def test_burst_not_triggered_after_eviction():
    d = BurstDetector(threshold=2, window_seconds=1.0)
    d.record(ts=0.0)
    d.record(ts=0.5)
    # Both evicted; only one new event — no burst
    result = d.record(ts=5.0)
    assert result is False


# ---------------------------------------------------------------------------
# current_window_count
# ---------------------------------------------------------------------------

def test_window_count_reflects_live_events():
    d = BurstDetector(threshold=10, window_seconds=5.0)
    d.record(ts=0.0)
    d.record(ts=1.0)
    d.record(ts=3.0)
    assert d.current_window_count(ts=4.0) == 3


def test_window_count_excludes_expired():
    d = BurstDetector(threshold=10, window_seconds=2.0)
    d.record(ts=0.0)
    d.record(ts=1.0)
    d.record(ts=5.0)
    # ts=0 and ts=1 are outside window at ts=5
    assert d.current_window_count(ts=5.0) == 1


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_clears_state():
    d = BurstDetector(threshold=1, window_seconds=10.0)
    d.record(ts=0.0)
    d.record(ts=1.0)  # burst
    d.reset()
    assert d.burst_count == 0
    assert d.current_window_count(ts=1.0) == 0


def test_after_reset_no_burst_on_fresh_events():
    d = BurstDetector(threshold=2, window_seconds=10.0)
    d.record(ts=0.0)
    d.record(ts=1.0)
    d.record(ts=2.0)  # burst
    d.reset()
    assert d.record(ts=3.0) is False
    assert d.record(ts=4.0) is False
