"""Join two JSON log streams on a shared key field."""

from __future__ import annotations

import json
from typing import Dict, Iterable, Iterator, List, Optional


class JoinError(Exception):
    """Raised for invalid join configuration or input."""


class JoinFilter:
    """Left-join records from a *right* iterable into a primary stream.

    For each primary record the join key is looked up in an in-memory
    index built from *right_lines*.  Matching fields are merged under an
    optional prefix so they never overwrite primary fields.

    Parameters
    ----------
    key:
        Dot-separated field path used as the join key in both streams.
    right_lines:
        Iterable of raw JSON strings that form the right-hand side.
    prefix:
        String prepended to every field imported from the right record.
        Defaults to ``"joined_"``.
    """

    def __init__(
        self,
        key: str,
        right_lines: Iterable[str],
        prefix: str = "joined_",
    ) -> None:
        if not key:
            raise JoinError("key must be a non-empty string")
        self._key = key
        self._prefix = prefix
        self._index: Dict[str, dict] = {}
        self._build_index(right_lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_field(self, record: dict, path: str) -> Optional[str]:
        """Return a dot-path field as a string key, or None if missing."""
        parts = path.split(".")
        node = record
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return str(node)

    def _build_index(self, lines: Iterable[str]) -> None:
        for raw in lines:
            raw = raw.rstrip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            key_val = self._get_field(record, self._key)
            if key_val is not None:
                self._index[key_val] = record

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def index_size(self) -> int:
        """Number of right-side records indexed."""
        return len(self._index)

    def join_record(self, record: dict) -> dict:
        """Return *record* enriched with matching right-side fields."""
        if not isinstance(record, dict):
            raise JoinError("record must be a dict")
        key_val = self._get_field(record, self._key)
        result = dict(record)
        if key_val is not None and key_val in self._index:
            right = self._index[key_val]
            for field, value in right.items():
                result[f"{self._prefix}{field}"] = value
        return result

    def process(self, lines: Iterable[str]) -> Iterator[str]:
        """Yield enriched JSON strings for each parseable line in *lines*."""
        for raw in lines:
            raw = raw.rstrip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            yield json.dumps(self.join_record(record))
