"""Convenience pipeline: parse JSON lines, apply PatternFilter, yield results."""

from __future__ import annotations

import json
from typing import Iterable, Iterator, List, Optional

from logslice.pattern_filter import PatternFilter, PatternFilterError


class PatternPipelineError(Exception):
    """Raised for unrecoverable pipeline configuration errors."""


class PatternPipeline:
    """Decode JSON lines and apply one or more PatternFilters in sequence.

    All filters must pass for a record to be emitted (AND semantics).
    """

    def __init__(self, filters: List[PatternFilter]) -> None:
        if not filters:
            raise PatternPipelineError("at least one PatternFilter is required")
        self._filters = filters
        self._decoded = 0
        self._emitted = 0
        self._skipped = 0

    @classmethod
    def from_spec(
        cls,
        field: str,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        ignore_case: bool = False,
    ) -> "PatternPipeline":
        """Convenience constructor for a single-filter pipeline."""
        try:
            pf = PatternFilter(
                field=field,
                include=include,
                exclude=exclude,
                ignore_case=ignore_case,
            )
        except PatternFilterError as exc:
            raise PatternPipelineError(str(exc)) from exc
        return cls([pf])

    @property
    def decoded_count(self) -> int:
        return self._decoded

    @property
    def emitted_count(self) -> int:
        return self._emitted

    @property
    def skipped_count(self) -> int:
        return self._skipped

    def process_lines(self, lines: Iterable[str]) -> Iterator[dict]:
        """Yield dicts that pass all filters; silently skip invalid JSON."""
        for raw in lines:
            raw = raw.rstrip("\n")
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                self._skipped += 1
                continue

            self._decoded += 1

            if all(f.matches(record) for f in self._filters):
                self._emitted += 1
                yield record

    def summary(self) -> dict:
        return {
            "decoded": self._decoded,
            "emitted": self._emitted,
            "skipped": self._skipped,
            "dropped": self._decoded - self._emitted,
        }
