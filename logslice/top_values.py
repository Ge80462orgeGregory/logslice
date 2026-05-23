"""top_values.py – collect and report the top-N most frequent values for a field."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple


class TopValuesError(ValueError):
    """Raised when TopValues is misconfigured."""


class TopValues:
    """Count field values across records and return the top-N most frequent."""

    def __init__(self, field: str, n: int = 10) -> None:
        if not field or not field.strip():
            raise TopValuesError("field must be a non-empty string")
        if n < 1:
            raise TopValuesError(f"n must be >= 1, got {n}")
        self._field = field
        self._n = n
        self._counter: Counter[str] = Counter()
        self._total = 0
        self._missing = 0

    @property
    def field(self) -> str:
        return self._field

    @property
    def n(self) -> int:
        return self._n

    @property
    def total(self) -> int:
        return self._total

    @property
    def missing(self) -> int:
        """Records where the field was absent or None."""
        return self._missing

    def _get_nested(self, record: Dict[str, Any], field: str) -> Optional[Any]:
        """Support dot-notation for nested fields."""
        parts = field.split(".")
        cur: Any = record
        for part in parts:
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
        return cur

    def feed(self, record: Any) -> None:
        """Feed a single parsed record (must be a dict)."""
        if not isinstance(record, dict):
            raise TopValuesError(f"record must be a dict, got {type(record).__name__}")
        self._total += 1
        value = self._get_nested(record, self._field)
        if value is None:
            self._missing += 1
        else:
            self._counter[str(value)] += 1

    def feed_many(self, records: Iterable[Any]) -> None:
        for rec in records:
            self.feed(rec)

    def top(self) -> List[Tuple[str, int]]:
        """Return the top-N (value, count) pairs, most frequent first."""
        return self._counter.most_common(self._n)

    def summary(self) -> Dict[str, Any]:
        return {
            "field": self._field,
            "n": self._n,
            "total": self._total,
            "missing": self._missing,
            "top": [{"value": v, "count": c} for v, c in self.top()],
        }
