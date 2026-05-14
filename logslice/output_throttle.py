"""OutputThrottle — integrates RateLimiter with the OutputFormatter pipeline.

Wraps an OutputFormatter and a RateLimiter so that lines exceeding the
configured rate are silently dropped (or optionally counted for stats).
"""

from __future__ import annotations

from typing import Optional

from logslice.output_formatter import OutputFormatter
from logslice.rate_limiter import RateLimiter, RateLimitExceeded


class OutputThrottle:
    """Wraps OutputFormatter with rate-limiting behaviour."""

    def __init__(
        self,
        formatter: OutputFormatter,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self._formatter = formatter
        self._limiter = rate_limiter
        self._dropped = 0
        self._emitted = 0

    def emit(self, raw_line: str) -> Optional[str]:
        """Format and emit *raw_line* if within rate limit.

        Returns the formatted string when emitted, or None when dropped.
        """
        if self._limiter is not None and not self._limiter.allow():
            self._dropped += 1
            return None

        formatted = self._formatter.format_line(raw_line)
        if formatted is not None:
            self._emitted += 1
        return formatted

    @property
    def dropped(self) -> int:
        """Total number of lines dropped due to rate limiting."""
        return self._dropped

    @property
    def emitted(self) -> int:
        """Total number of lines successfully emitted."""
        return self._emitted

    def reset_counters(self) -> None:
        """Reset dropped and emitted counters (does not reset the limiter)."""
        self._dropped = 0
        self._emitted = 0
