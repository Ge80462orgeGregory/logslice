"""Filter JSON log records by the length of a string field value."""

from __future__ import annotations

from typing import Any, Optional


class LengthFilterError(Exception):
    """Raised when LengthFilter is misconfigured."""


def _get_nested(record: dict, field: str) -> Any:
    """Resolve a dot-separated field path from a dict."""
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


class LengthFilter:
    """Keep records where *field* string length satisfies the given bounds.

    At least one of *min_len* or *max_len* must be provided.
    """

    def __init__(
        self,
        field: str,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None,
    ) -> None:
        if not field:
            raise LengthFilterError("field must be a non-empty string")
        if min_len is None and max_len is None:
            raise LengthFilterError("at least one of min_len or max_len must be set")
        if min_len is not None and min_len < 0:
            raise LengthFilterError("min_len must be >= 0")
        if max_len is not None and max_len < 0:
            raise LengthFilterError("max_len must be >= 0")
        if min_len is not None and max_len is not None and min_len > max_len:
            raise LengthFilterError("min_len must not exceed max_len")
        self._field = field
        self._min_len = min_len
        self._max_len = max_len

    @property
    def field(self) -> str:
        return self._field

    @property
    def min_len(self) -> Optional[int]:
        return self._min_len

    @property
    def max_len(self) -> Optional[int]:
        return self._max_len

    def matches(self, record: dict) -> bool:
        """Return True if *record* passes the length constraint."""
        if not isinstance(record, dict):
            raise LengthFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if value is None:
            return False
        if not isinstance(value, str):
            return False
        length = len(value)
        if self._min_len is not None and length < self._min_len:
            return False
        if self._max_len is not None and length > self._max_len:
            return False
        return True

    def filter_records(self, records):
        """Yield records that satisfy the length constraint."""
        for record in records:
            if self.matches(record):
                yield record
