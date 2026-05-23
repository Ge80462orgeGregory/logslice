"""Filter JSON log records by numeric field ranges."""

from __future__ import annotations

from typing import Any, Optional


class NumericFilterError(Exception):
    """Raised when NumericFilter is misconfigured or encounters bad input."""


def _get_nested(record: dict, field: str) -> Any:
    """Retrieve a possibly dot-separated nested field value."""
    parts = field.split(".")
    current: Any = record
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


class NumericFilter:
    """Pass records where a numeric field satisfies optional min/max bounds.

    At least one of *min_val* or *max_val* must be provided.
    Bounds are inclusive.
    Records where the field is absent or non-numeric are dropped.
    """

    def __init__(
        self,
        field: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> None:
        if not field:
            raise NumericFilterError("field must be a non-empty string")
        if min_val is None and max_val is None:
            raise NumericFilterError("at least one of min_val or max_val must be set")
        if min_val is not None and max_val is not None and min_val > max_val:
            raise NumericFilterError(
                f"min_val ({min_val}) must not exceed max_val ({max_val})"
            )
        self._field = field
        self._min = min_val
        self._max = max_val

    @property
    def field(self) -> str:
        return self._field

    @property
    def min_val(self) -> Optional[float]:
        return self._min

    @property
    def max_val(self) -> Optional[float]:
        return self._max

    def matches(self, record: dict) -> bool:
        """Return True if *record* passes the numeric range check."""
        if not isinstance(record, dict):
            raise NumericFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if value is None:
            return False
        if not isinstance(value, (int, float)):
            return False
        if self._min is not None and value < self._min:
            return False
        if self._max is not None and value > self._max:
            return False
        return True

    def filter_many(self, records: list[dict]) -> list[dict]:
        """Return only records that pass *matches*."""
        return [r for r in records if self.matches(r)]
