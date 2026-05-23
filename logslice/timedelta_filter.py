"""Filter JSON log records by a relative time window (e.g. 'last 5m')."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


class TimedeltaFilterError(Exception):  # noqa: N818
    """Raised for invalid configuration or unparseable durations."""


_UNIT_MAP: Dict[str, str] = {
    "s": "seconds",
    "sec": "seconds",
    "m": "minutes",
    "min": "minutes",
    "h": "hours",
    "hr": "hours",
    "d": "days",
}

_DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*([a-zA-Z]+)$")


def parse_duration(raw: str) -> timedelta:
    """Parse a human duration string like '5m', '2h', '30s' into a timedelta."""
    m = _DURATION_RE.match(raw.strip())
    if not m:
        raise TimedeltaFilterError(f"Cannot parse duration: {raw!r}")
    amount, unit = float(m.group(1)), m.group(2).lower()
    if unit not in _UNIT_MAP:
        raise TimedeltaFilterError(
            f"Unknown time unit {unit!r}. Use one of: {', '.join(_UNIT_MAP)}"
        )
    return timedelta(**{_UNIT_MAP[unit]: amount})


class TimedeltaFilter:
    """Keep records whose timestamp field falls within *now - window* to now."""

    def __init__(
        self,
        window: str,
        field: str = "timestamp",
        now: Optional[datetime] = None,
    ) -> None:
        if not field:
            raise TimedeltaFilterError("field must not be empty")
        self._delta = parse_duration(window)
        self._field = field
        self._now = now  # injectable for testing

    @property
    def field(self) -> str:
        return self._field

    @property
    def window(self) -> timedelta:
        return self._delta

    def _now_utc(self) -> datetime:
        if self._now is not None:
            return self._now
        return datetime.now(tz=timezone.utc)

    def _parse_ts(self, value: Any) -> Optional[datetime]:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if isinstance(value, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z",
                        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(value, fmt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue
        return None

    def matches(self, record: Dict[str, Any]) -> bool:
        """Return True if the record's timestamp is within the configured window."""
        raw = record.get(self._field)
        if raw is None:
            return False
        dt = self._parse_ts(raw)
        if dt is None:
            return False
        cutoff = self._now_utc() - self._delta
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)
        return dt >= cutoff

    def filter_records(self, records):
        """Yield records that fall within the time window."""
        for record in records:
            if self.matches(record):
                yield record
