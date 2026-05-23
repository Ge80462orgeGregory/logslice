"""High-level pipeline: filter records then build a histogram."""

from __future__ import annotations

from typing import Iterable, List, Optional

from logslice.filter_engine import FilterEngine
from logslice.histogram import Histogram, HistogramError


class HistogramPipelineError(Exception):
    """Raised when the pipeline is misconfigured."""


class HistogramPipeline:
    """Filter JSON records, then accumulate a histogram over a numeric field."""

    def __init__(
        self,
        field: str,
        bucket_size: float,
        queries: Optional[List[str]] = None,
    ) -> None:
        try:
            self._histogram = Histogram(field=field, bucket_size=bucket_size)
        except HistogramError as exc:
            raise HistogramPipelineError(str(exc)) from exc

        self._engine = FilterEngine()
        for q in queries or []:
            try:
                self._engine.add_query(q)
            except Exception as exc:
                raise HistogramPipelineError(f"invalid query {q!r}: {exc}") from exc

        self._decoded = 0
        self._filtered = 0

    @property
    def decoded_count(self) -> int:
        """Number of records successfully decoded and evaluated."""
        return self._decoded

    @property
    def filtered_count(self) -> int:
        """Number of records that passed all filters."""
        return self._filtered

    @property
    def histogram(self) -> Histogram:
        return self._histogram

    def process(self, record: dict) -> bool:
        """Feed one record through the pipeline. Returns True if it was counted."""
        if not isinstance(record, dict):
            return False
        self._decoded += 1
        if not self._engine.matches(record):
            return False
        self._filtered += 1
        self._histogram.feed(record)
        return True

    def process_many(self, records: Iterable[dict]) -> None:
        for record in records:
            self.process(record)

    def render(self, bar_width: int = 40) -> str:
        lines = [
            self._histogram.render(bar_width=bar_width),
            f"\ndecoded: {self._decoded}  filtered: {self._filtered}"
            f"  counted: {self._histogram.total}  skipped: {self._histogram.skipped}",
        ]
        return "\n".join(lines)
