"""Time-range filtering for structured JSON log lines."""

from __future__ import annotations

import datetime
from typing import Optional


class TimeFilterError(Exception):
    """Raised when a time filter cannot be constructed or applied."""


_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d",
]


def _parse_dt(value: str) -> datetime.datetime:
    """Try several common ISO-ish formats and return a naive datetime."""
    for fmt in _FORMATS:
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise TimeFilterError(
        f"Cannot parse timestamp {value!r}. "
        f"Accepted formats: {', '.join(_FORMATS)}"
    )


class TimeFilter:
    """Filter log records by a timestamp field falling within [since, until].

    Parameters
    ----------
    field:
        Dot-separated key path to the timestamp value inside each record.
    since:
        Inclusive lower bound (string or datetime).  ``None`` means no lower bound.
    until:
        Inclusive upper bound (string or datetime).  ``None`` means no upper bound.
    """

    def __init__(
        self,
        field: str = "timestamp",
        since: Optional[str | datetime.datetime] = None,
        until: Optional[str | datetime.datetime] = None,
    ) -> None:
        if not field:
            raise TimeFilterError("field must not be empty")
        if since is None and until is None:
            raise TimeFilterError("At least one of 'since' or 'until' must be provided")

        self.field = field
        self.since: Optional[datetime.datetime] = (
            _parse_dt(since) if isinstance(since, str) else since
        )
        self.until: Optional[datetime.datetime] = (
            _parse_dt(until) if isinstance(until, str) else until
        )

        if self.since and self.until and self.since > self.until:
            raise TimeFilterError("'since' must not be later than 'until'")

    def _get_field(self, record: dict) -> Optional[datetime.datetime]:
        """Resolve dot-separated field path and parse to datetime."""
        parts = self.field.split(".")
        node = record
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        if not isinstance(node, str):
            return None
        try:
            return _parse_dt(node)
        except TimeFilterError:
            return None

    def matches(self, record: dict) -> bool:
        """Return True when *record* falls within the configured time window."""
        ts = self._get_field(record)
        if ts is None:
            return False
        if self.since and ts < self.since:
            return False
        if self.until and ts > self.until:
            return False
        return True
