"""Filter records where a numeric field crosses a configurable threshold."""

from __future__ import annotations

from typing import Any, Optional


class ThresholdFilterError(Exception):
    """Raised for invalid ThresholdFilter configuration."""


def _get_nested(record: dict, field: str) -> Any:
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


class ThresholdFilter:
    """Keep records where *field* is above, below, or equal to *threshold*.

    Parameters
    ----------
    field:
        Dot-separated path to the numeric field.
    threshold:
        The numeric boundary value.
    direction:
        One of ``'above'``, ``'below'``, or ``'equal'``.
    inclusive:
        When *True* the boundary value itself passes (>=, <=, ==).
    invert:
        When *True* the sense of the filter is reversed.
    """

    _DIRECTIONS = frozenset({"above", "below", "equal"})

    def __init__(
        self,
        field: str,
        threshold: float,
        direction: str = "above",
        *,
        inclusive: bool = True,
        invert: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise ThresholdFilterError("field must not be empty")
        if direction not in self._DIRECTIONS:
            raise ThresholdFilterError(
                f"direction must be one of {sorted(self._DIRECTIONS)}, got {direction!r}"
            )
        self._field = field.strip()
        self._threshold = float(threshold)
        self._direction = direction
        self._inclusive = inclusive
        self._invert = invert

    @property
    def field(self) -> str:
        return self._field

    @property
    def threshold(self) -> float:
        return self._threshold

    @property
    def direction(self) -> str:
        return self._direction

    @property
    def inclusive(self) -> bool:
        return self._inclusive

    @property
    def invert(self) -> bool:
        return self._invert

    def matches(self, record: dict) -> bool:
        if not isinstance(record, dict):
            raise ThresholdFilterError("record must be a dict")
        raw = _get_nested(record, self._field)
        if raw is None:
            return False
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return False
        t = self._threshold
        if self._direction == "above":
            result = value >= t if self._inclusive else value > t
        elif self._direction == "below":
            result = value <= t if self._inclusive else value < t
        else:  # equal
            result = value == t
        return result if not self._invert else not result
