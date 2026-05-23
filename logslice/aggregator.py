"""Field-value aggregation for structured JSON log records."""

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional


class AggregatorError(Exception):
    """Raised when aggregation is misconfigured or fails."""


class Aggregator:
    """Counts occurrences of distinct values for one or more fields.

    Example::

        agg = Aggregator(fields=["level", "service"])
        for record in records:
            agg.feed(record)
        print(agg.top("level", n=5))
    """

    def __init__(self, fields: List[str]) -> None:
        if not fields:
            raise AggregatorError("At least one field must be specified.")
        self._fields: List[str] = fields
        self._counts: Dict[str, Dict[Any, int]] = {
            f: defaultdict(int) for f in fields
        }
        self._total: int = 0

    # ------------------------------------------------------------------
    def feed(self, record: Dict[str, Any]) -> None:
        """Ingest a single parsed log record."""
        if not isinstance(record, dict):
            raise AggregatorError("record must be a dict.")
        self._total += 1
        for field in self._fields:
            value = record.get(field)
            if value is not None:
                self._counts[field][value] += 1

    def feed_many(self, records: Iterable[Dict[str, Any]]) -> None:
        """Ingest multiple records."""
        for record in records:
            self.feed(record)

    # ------------------------------------------------------------------
    def counts(self, field: str) -> Dict[Any, int]:
        """Return the full value-count mapping for *field*."""
        if field not in self._counts:
            raise AggregatorError(f"Field {field!r} is not tracked.")
        return dict(self._counts[field])

    def top(self, field: str, n: int = 10) -> List[tuple]:
        """Return the top-*n* (value, count) pairs sorted by count desc."""
        return sorted(
            self.counts(field).items(), key=lambda kv: kv[1], reverse=True
        )[:n]

    def coverage(self, field: str) -> float:
        """Return the fraction of total records that contained *field*.

        Returns a float in the range [0.0, 1.0], or 0.0 when no records
        have been fed yet.
        """
        if self._total == 0:
            return 0.0
        present = sum(self._counts[field].values()) if field in self._counts else 0
        if field not in self._counts:
            raise AggregatorError(f"Field {field!r} is not tracked.")
        return present / self._total

    @property
    def total(self) -> int:
        """Total number of records fed."""
        return self._total

    def summary(self) -> Dict[str, Any]:
        """Return a dict summary suitable for display or serialisation."""
        return {
            "total": self._total,
            "fields": {
                field: self.top(field) for field in self._fields
            },
        }
