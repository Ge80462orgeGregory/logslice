"""Collects and summarizes statistics from processed log lines."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional


class StatsCollector:
    """Accumulates statistics over a stream of parsed JSON log records."""

    def __init__(self, count_fields: Optional[List[str]] = None) -> None:
        """
        Args:
            count_fields: Field names whose distinct values should be counted.
        """
        self.count_fields: List[str] = count_fields or []
        self.total: int = 0
        self.matched: int = 0
        self._field_counters: Dict[str, Counter] = defaultdict(Counter)

    def record(self, record: Dict[str, Any], *, matched: bool = True) -> None:
        """Register a single log record.

        Args:
            record: Parsed JSON object.
            matched: Whether the record passed the active filter.
        """
        self.total += 1
        if matched:
            self.matched += 1
            for field in self.count_fields:
                value = record.get(field)
                if value is not None:
                    self._field_counters[field][str(value)] += 1

    def field_counts(self, field: str) -> Dict[str, int]:
        """Return value-frequency mapping for *field*."""
        return dict(self._field_counters.get(field, {}))

    def summary(self) -> Dict[str, Any]:
        """Return a plain-dict summary suitable for display or serialisation."""
        result: Dict[str, Any] = {
            "total": self.total,
            "matched": self.matched,
            "dropped": self.total - self.matched,
        }
        for field in self.count_fields:
            result[f"counts:{field}"] = self.field_counts(field)
        return result

    def reset(self) -> None:
        """Clear all accumulated data."""
        self.total = 0
        self.matched = 0
        self._field_counters.clear()
