"""Deduplication filter for structured JSON log lines."""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Iterable, Iterator, List, Optional


class DedupError(Exception):
    """Raised when the deduplication filter is misconfigured."""


class DedupFilter:
    """Suppress duplicate log records within a sliding window.

    Two records are considered duplicates when the values of *fields*
    (or the entire serialised record when *fields* is empty) are identical.

    Parameters
    ----------
    fields:
        Dot-separated field names used to compute the dedup key.  When
        empty the whole record is hashed.
    window:
        Maximum number of unique keys kept in memory.  The oldest entry
        is evicted once the window is full (LRU eviction).
    """

    def __init__(self, fields: Optional[List[str]] = None, window: int = 1000) -> None:
        if window < 1:
            raise DedupError(f"window must be >= 1, got {window}")
        self._fields: List[str] = fields or []
        self._window = window
        self._seen: OrderedDict[str, None] = OrderedDict()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def window(self) -> int:
        return self._window

    @property
    def seen_count(self) -> int:
        return len(self._seen)

    def _key(self, record: dict) -> str:
        if self._fields:
            parts = {f: self._get_nested(record, f) for f in self._fields}
            raw = json.dumps(parts, sort_keys=True, default=str)
        else:
            raw = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha1(raw.encode()).hexdigest()  # noqa: S324

    @staticmethod
    def _get_nested(record: dict, field: str):
        parts = field.split(".")
        node = record
        for part in parts:
            if not isinstance(node, dict):
                return None
            node = node.get(part)
        return node

    def is_duplicate(self, record: dict) -> bool:
        """Return *True* if *record* is a duplicate and should be dropped."""
        key = self._key(record)
        if key in self._seen:
            self._seen.move_to_end(key)
            return True
        self._seen[key] = None
        if len(self._seen) > self._window:
            self._seen.popitem(last=False)
        return False

    def filter_records(self, records: Iterable[dict]) -> Iterator[dict]:
        """Yield only non-duplicate records from *records*."""
        for record in records:
            if not self.is_duplicate(record):
                yield record

    def reset(self) -> None:
        """Clear the internal seen-key cache."""
        self._seen.clear()
