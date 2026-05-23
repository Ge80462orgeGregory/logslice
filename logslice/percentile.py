"""Percentile calculator for numeric fields in JSON log records."""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Tuple


class PercentileError(Exception):
    """Raised when Percentile is misconfigured or receives invalid input."""


class Percentile:
    """Collect numeric values for a field and compute percentile statistics."""

    def __init__(self, field: str, percentiles: Optional[List[float]] = None) -> None:
        if not field:
            raise PercentileError("field must be a non-empty string")
        _pcts = percentiles if percentiles is not None else [50.0, 90.0, 95.0, 99.0]
        for p in _pcts:
            if not (0.0 <= p <= 100.0):
                raise PercentileError(f"percentile {p} is out of range [0, 100]")
        self._field = field
        self._percentiles = _pcts
        self._values: List[float] = []
        self._skipped = 0

    @property
    def field(self) -> str:
        return self._field

    @property
    def requested(self) -> List[float]:
        return list(self._percentiles)

    @property
    def count(self) -> int:
        return len(self._values)

    @property
    def skipped(self) -> int:
        return self._skipped

    def feed(self, record: dict) -> None:
        if not isinstance(record, dict):
            raise PercentileError("record must be a dict")
        raw = record.get(self._field)
        if raw is None:
            self._skipped += 1
            return
        try:
            self._values.append(float(raw))
        except (TypeError, ValueError):
            self._skipped += 1

    def feed_many(self, records: Iterable[dict]) -> None:
        for record in records:
            self.feed(record)

    def compute(self) -> Dict[float, float]:
        """Return a mapping of percentile -> value.  Raises if no data."""
        if not self._values:
            raise PercentileError("no numeric values collected; cannot compute percentiles")
        sorted_vals = sorted(self._values)
        n = len(sorted_vals)
        result: Dict[float, float] = {}
        for p in self._percentiles:
            if p == 0.0:
                result[p] = sorted_vals[0]
            elif p == 100.0:
                result[p] = sorted_vals[-1]
            else:
                rank = (p / 100.0) * n
                lower = math.floor(rank) - 1
                upper = math.ceil(rank) - 1
                lower = max(lower, 0)
                upper = min(upper, n - 1)
                if lower == upper:
                    result[p] = sorted_vals[lower]
                else:
                    result[p] = (sorted_vals[lower] + sorted_vals[upper]) / 2.0
        return result

    def summary(self) -> List[Tuple[float, float]]:
        """Return sorted list of (percentile, value) tuples."""
        computed = self.compute()
        return sorted(computed.items())
