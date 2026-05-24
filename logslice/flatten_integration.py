"""Integration helper: flatten nested records then pass through a FilterEngine."""
from __future__ import annotations

from typing import Iterable, Iterator, List, Optional

from logslice.field_extractor import flatten_record, FieldExtractorError
from logslice.filter_engine import FilterEngine


class FlattenPipelineError(Exception):
    """Raised when the pipeline is misconfigured."""


class FlattenPipeline:
    """Flatten JSON records and optionally apply filter queries.

    Parameters
    ----------
    separator:
        Key separator used when flattening (default ``'.'``).
    prefix:
        Optional prefix prepended to every flattened key.
    queries:
        Optional list of query strings forwarded to :class:`FilterEngine`.
    skip_errors:
        When *True*, records that fail to flatten are silently dropped.
    """

    def __init__(
        self,
        separator: str = ".",
        prefix: str = "",
        queries: Optional[List[str]] = None,
        skip_errors: bool = False,
    ) -> None:
        self._separator = separator
        self._prefix = prefix
        self._skip_errors = skip_errors
        self._engine: Optional[FilterEngine] = None
        if queries:
            self._engine = FilterEngine()
            for q in queries:
                self._engine.add_query(q)
        self._decoded = 0
        self._filtered = 0

    @property
    def decoded_count(self) -> int:
        """Total records successfully flattened."""
        return self._decoded

    @property
    def filtered_count(self) -> int:
        """Records that passed the filter (or all decoded if no filter)."""
        return self._filtered

    def process(
        self, records: Iterable[dict]
    ) -> Iterator[dict]:
        """Yield flattened (and optionally filtered) records."""
        for record in records:
            try:
                flat = flatten_record(
                    record,
                    separator=self._separator,
                    prefix=self._prefix,
                )
            except FieldExtractorError:
                if self._skip_errors:
                    continue
                raise
            self._decoded += 1
            if self._engine is None or self._engine.matches(flat):
                self._filtered += 1
                yield flat
