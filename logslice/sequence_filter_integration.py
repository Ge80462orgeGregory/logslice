"""Pipeline integration: decode JSON lines, apply SequenceFilter, yield results."""
from __future__ import annotations

import json
from typing import Iterator

from logslice.sequence_filter import SequenceFilter, SequenceFilterError


class SequencePipelineError(Exception):
    """Raised for invalid pipeline configuration."""


class SequencePipeline:
    """Decode JSON lines and keep only those maintaining a numeric sequence."""

    def __init__(self, field: str, *, decreasing: bool = False) -> None:
        try:
            self._sf = SequenceFilter(field, decreasing=decreasing)
        except SequenceFilterError as exc:
            raise SequencePipelineError(str(exc)) from exc
        self._decoded = 0
        self._passed = 0

    @property
    def decoded_count(self) -> int:
        return self._decoded

    @property
    def passed_count(self) -> int:
        return self._passed

    @property
    def dropped_count(self) -> int:
        return self._decoded - self._passed

    def process_lines(self, lines: list[str]) -> Iterator[dict]:
        """Yield dicts that pass the sequence filter."""
        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            self._decoded += 1
            try:
                if self._sf.keep(record):
                    self._passed += 1
                    yield record
            except SequenceFilterError:
                continue

    def reset(self) -> None:
        """Reset filter state and counters."""
        self._sf.reset()
        self._decoded = 0
        self._passed = 0
