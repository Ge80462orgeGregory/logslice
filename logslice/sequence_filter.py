"""Filter records where a numeric field value is monotonically increasing or decreasing."""
from __future__ import annotations

from typing import Any, Optional


class SequenceFilterError(Exception):
    """Raised for invalid SequenceFilter configuration."""


def _get_nested(record: dict, field: str) -> Any:
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


class SequenceFilter:
    """Pass only records where *field* is strictly increasing (or decreasing).

    Non-numeric values and records where the field is absent are dropped.
    The first valid record always passes.
    """

    def __init__(self, field: str, *, decreasing: bool = False) -> None:
        if not field or not field.strip():
            raise SequenceFilterError("field must be a non-empty string")
        self._field = field.strip()
        self._decreasing = decreasing
        self._last: Optional[float] = None

    @property
    def field(self) -> str:
        return self._field

    @property
    def decreasing(self) -> bool:
        return self._decreasing

    @property
    def last_value(self) -> Optional[float]:
        return self._last

    def reset(self) -> None:
        """Reset the tracked last value."""
        self._last = None

    def keep(self, record: dict) -> bool:
        """Return True if *record* should be kept."""
        if not isinstance(record, dict):
            raise SequenceFilterError("record must be a dict")
        raw = _get_nested(record, self._field)
        if raw is None:
            return False
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return False
        if self._last is None:
            self._last = value
            return True
        if self._decreasing:
            result = value < self._last
        else:
            result = value > self._last
        if result:
            self._last = value
        return result

    def filter(self, records: list[dict]) -> list[dict]:
        """Return only records that maintain the required sequence."""
        return [r for r in records if self.keep(r)]
