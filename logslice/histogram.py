"""Histogram: bucket numeric or datetime field values across log records."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple


class HistogramError(Exception):
    """Raised for invalid histogram configuration or input."""


class Histogram:
    """Accumulate counts of a numeric field into fixed-width buckets."""

    def __init__(self, field: str, bucket_size: float) -> None:
        if not field:
            raise HistogramError("field must be a non-empty string")
        if bucket_size <= 0:
            raise HistogramError("bucket_size must be a positive number")
        self._field = field
        self._bucket_size = bucket_size
        self._counts: Dict[float, int] = defaultdict(int)
        self._total = 0
        self._skipped = 0

    @property
    def field(self) -> str:
        return self._field

    @property
    def bucket_size(self) -> float:
        return self._bucket_size

    @property
    def total(self) -> int:
        return self._total

    @property
    def skipped(self) -> int:
        return self._skipped

    def _get_value(self, record: dict) -> Optional[float]:
        parts = self._field.split(".")
        node = record
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        try:
            return float(node)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    def _bucket_key(self, value: float) -> float:
        return math.floor(value / self._bucket_size) * self._bucket_size

    def feed(self, record: dict) -> None:
        if not isinstance(record, dict):
            raise HistogramError("record must be a dict")
        value = self._get_value(record)
        if value is None:
            self._skipped += 1
            return
        self._counts[self._bucket_key(value)] += 1
        self._total += 1

    def feed_many(self, records: Iterable[dict]) -> None:
        for record in records:
            self.feed(record)

    def buckets(self) -> List[Tuple[float, float, int]]:
        """Return sorted list of (bucket_start, bucket_end, count) triples."""
        return [
            (key, key + self._bucket_size, count)
            for key, count in sorted(self._counts.items())
        ]

    def render(self, bar_width: int = 40) -> str:
        """Return a simple ASCII bar-chart string."""
        rows = self.buckets()
        if not rows:
            return "(no data)"
        max_count = max(c for _, _, c in rows)
        lines: List[str] = []
        for start, end, count in rows:
            bar_len = int(bar_width * count / max_count) if max_count else 0
            bar = "#" * bar_len
            lines.append(f"[{start:>10.2f}, {end:>10.2f}) | {bar:<{bar_width}} {count}")
        return "\n".join(lines)
