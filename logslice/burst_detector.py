"""Detect bursts of log lines exceeding a threshold within a sliding time window."""

from __future__ import annotations

import time
from collections import deque
from typing import Deque


class BurstDetectorError(Exception):
    """Raised for invalid BurstDetector configuration."""


class BurstDetector:
    """Tracks log-line arrival times and flags bursts.

    A burst is detected when more than *threshold* lines arrive within
    *window_seconds* seconds.
    """

    def __init__(self, threshold: int, window_seconds: float) -> None:
        if threshold < 1:
            raise BurstDetectorError("threshold must be >= 1")
        if window_seconds <= 0:
            raise BurstDetectorError("window_seconds must be > 0")
        self._threshold = threshold
        self._window = window_seconds
        self._timestamps: Deque[float] = deque()
        self._burst_count = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def threshold(self) -> int:
        return self._threshold

    @property
    def window_seconds(self) -> float:
        return self._window

    @property
    def burst_count(self) -> int:
        """Total number of bursts detected so far."""
        return self._burst_count

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, ts: float | None = None) -> bool:
        """Record a new line arrival.

        Parameters
        ----------
        ts:
            Epoch timestamp of the line; defaults to ``time.monotonic()``.

        Returns
        -------
        bool
            ``True`` if this arrival triggered a burst (i.e. the window
            now contains more than *threshold* events).
        """
        now = ts if ts is not None else time.monotonic()
        self._evict(now)
        self._timestamps.append(now)
        if len(self._timestamps) > self._threshold:
            self._burst_count += 1
            return True
        return False

    def current_window_count(self, ts: float | None = None) -> int:
        """Return the number of events still inside the sliding window."""
        now = ts if ts is not None else time.monotonic()
        self._evict(now)
        return len(self._timestamps)

    def reset(self) -> None:
        """Clear all recorded timestamps and burst counters."""
        self._timestamps.clear()
        self._burst_count = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict(self, now: float) -> None:
        cutoff = now - self._window
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()
