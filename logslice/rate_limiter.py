"""Rate limiter for logslice — throttles output to a maximum number of lines per second."""

import time
from collections import deque


class RateLimitExceeded(Exception):
    """Raised when the rate limit has been exceeded and a line should be dropped."""
    pass


class RateLimiter:
    """Sliding-window rate limiter.

    Tracks timestamps of recently emitted lines and raises RateLimitExceeded
    when the configured maximum lines-per-second threshold is breached.
    """

    def __init__(self, max_lines_per_second: int, window_seconds: float = 1.0):
        if max_lines_per_second <= 0:
            raise ValueError("max_lines_per_second must be a positive integer")
        self._max = max_lines_per_second
        self._window = window_seconds
        self._timestamps: deque = deque()

    def allow(self) -> bool:
        """Return True if the current line is within the rate limit, False otherwise."""
        now = time.monotonic()
        cutoff = now - self._window

        # Evict timestamps outside the sliding window
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        if len(self._timestamps) >= self._max:
            return False

        self._timestamps.append(now)
        return True

    def check(self) -> None:
        """Like allow(), but raises RateLimitExceeded when the limit is breached."""
        if not self.allow():
            raise RateLimitExceeded(
                f"Rate limit of {self._max} lines/s exceeded"
            )

    @property
    def current_count(self) -> int:
        """Number of lines recorded within the current window."""
        now = time.monotonic()
        cutoff = now - self._window
        return sum(1 for ts in self._timestamps if ts >= cutoff)

    def reset(self) -> None:
        """Clear all recorded timestamps."""
        self._timestamps.clear()
