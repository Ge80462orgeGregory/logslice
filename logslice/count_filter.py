"""Filter records by occurrence count of a field value."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterator, Optional


class CountFilterError(Exception):
    """Raised for invalid CountFilter configuration."""


def _get_nested(record: Dict[str, Any], field: str) -> Any:
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


class CountFilter:
    """Keep or drop records based on how many times a field value has been seen."""

    def __init__(
        self,
        field: str,
        min_count: Optional[int] = None,
        max_count: Optional[int] = None,
        invert: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise CountFilterError("field must be a non-empty string")
        if min_count is None and max_count is None:
            raise CountFilterError("at least one of min_count or max_count must be set")
        if min_count is not None and min_count < 1:
            raise CountFilterError("min_count must be >= 1")
        if max_count is not None and max_count < 1:
            raise CountFilterError("max_count must be >= 1")
        if min_count is not None and max_count is not None and min_count > max_count:
            raise CountFilterError("min_count must not exceed max_count")
        self._field = field.strip()
        self._min = min_count
        self._max = max_count
        self._invert = invert
        self._counts: Dict[Any, int] = defaultdict(int)

    @property
    def field(self) -> str:
        return self._field

    @property
    def min_count(self) -> Optional[int]:
        return self._min

    @property
    def max_count(self) -> Optional[int]:
        return self._max

    @property
    def invert(self) -> bool:
        return self._invert

    def seen_counts(self) -> Dict[Any, int]:
        return dict(self._counts)

    def matches(self, record: Dict[str, Any]) -> bool:
        if not isinstance(record, dict):
            raise CountFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        self._counts[value] += 1
        count = self._counts[value]
        in_range = (
            (self._min is None or count >= self._min)
            and (self._max is None or count <= self._max)
        )
        return in_range if not self._invert else not in_range

    def filter(self, records: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        for record in records:
            if self.matches(record):
                yield record
