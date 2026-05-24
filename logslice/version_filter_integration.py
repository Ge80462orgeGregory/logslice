"""Pipeline integration: decode JSON lines and apply VersionFilter."""
from __future__ import annotations

import json
from typing import Iterable, Iterator

from logslice.version_filter import VersionFilter, VersionFilterError


class VersionPipelineError(Exception):
    """Raised for misconfigured VersionPipeline."""


class VersionPipeline:
    """Wraps VersionFilter to process raw text lines.

    Tracks decoded, matched, and skipped (non-JSON / non-dict) counts.
    """

    def __init__(self, version_filter: VersionFilter) -> None:
        if not isinstance(version_filter, VersionFilter):
            raise VersionPipelineError("version_filter must be a VersionFilter instance")
        self._filter = version_filter
        self._decoded = 0
        self._matched = 0
        self._skipped = 0

    @classmethod
    def from_spec(
        cls,
        field: str,
        min_ver: str | None = None,
        max_ver: str | None = None,
        invert: bool = False,
    ) -> "VersionPipeline":
        try:
            vf = VersionFilter(field=field, min_ver=min_ver, max_ver=max_ver, invert=invert)
        except VersionFilterError as exc:
            raise VersionPipelineError(str(exc)) from exc
        return cls(vf)

    @property
    def decoded_count(self) -> int:
        return self._decoded

    @property
    def matched_count(self) -> int:
        return self._matched

    @property
    def skipped_count(self) -> int:
        return self._skipped

    def process_lines(self, lines: Iterable[str]) -> Iterator[dict]:
        for raw in lines:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                self._skipped += 1
                continue
            if not isinstance(record, dict):
                self._skipped += 1
                continue
            self._decoded += 1
            if self._filter.matches(record):
                self._matched += 1
                yield record

    def process_many(self, lines: Iterable[str]) -> list[dict]:
        return list(self.process_lines(lines))
