"""Tumbling-window aggregation over a numeric field in JSON log records."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Tuple


class WindowAggError(Exception):
    """Raised when WindowAgg is misconfigured."""


def _get_nested(record: dict, field: str):
    """Resolve a dot-separated field path; return None if missing."""
    parts = field.split(".")
    cur = record
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


class WindowAgg:
    """Aggregate a numeric field into fixed-size tumbling windows.

    Parameters
    ----------
    field:      dot-separated field path whose numeric value is bucketed.
    window:     bucket width (must be > 0).
    stats:      iterable of stat names to compute: 'count', 'sum', 'min', 'max', 'mean'.
    """

    _VALID_STATS = frozenset({"count", "sum", "min", "max", "mean"})

    def __init__(self, field: str, window: float, stats: List[str]) -> None:
        if not field or not field.strip():
            raise WindowAggError("field must not be empty")
        if window <= 0:
            raise WindowAggError("window must be greater than zero")
        unknown = set(stats) - self._VALID_STATS
        if unknown:
            raise WindowAggError(f"unknown stats: {sorted(unknown)}")
        if not stats:
            raise WindowAggError("at least one stat must be requested")
        self._field = field.strip()
        self._window = window
        self._stats = list(stats)
        self._buckets: Dict[float, List[float]] = defaultdict(list)
        self._skipped = 0

    @property
    def field(self) -> str:
        return self._field

    @property
    def window(self) -> float:
        return self._window

    @property
    def skipped(self) -> int:
        return self._skipped

    def _bucket_key(self, value: float) -> float:
        import math
        return math.floor(value / self._window) * self._window

    def feed(self, record: dict) -> None:
        if not isinstance(record, dict):
            raise WindowAggError("record must be a dict")
        raw = _get_nested(record, self._field)
        if raw is None:
            self._skipped += 1
            return
        try:
            value = float(raw)
        except (TypeError, ValueError):
            self._skipped += 1
            return
        self._buckets[self._bucket_key(value)].append(value)

    def results(self) -> List[Tuple[float, Dict[str, float]]]:
        """Return sorted list of (bucket_start, {stat: value}) pairs."""
        out = []
        for key in sorted(self._buckets):
            vals = self._buckets[key]
            row: Dict[str, float] = {}
            if "count" in self._stats:
                row["count"] = float(len(vals))
            if "sum" in self._stats:
                row["sum"] = sum(vals)
            if "min" in self._stats:
                row["min"] = min(vals)
            if "max" in self._stats:
                row["max"] = max(vals)
            if "mean" in self._stats:
                row["mean"] = sum(vals) / len(vals)
            out.append((key, row))
        return out
