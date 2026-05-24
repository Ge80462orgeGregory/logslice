"""Filter records by evaluating a JSONPath-style dotted field expression against a set of allowed values."""
from __future__ import annotations

from typing import Any, Iterable, List, Optional


class JsonPathFilterError(ValueError):
    """Raised when JsonPathFilter is misconfigured."""


def _get_nested(record: dict, path: str) -> Any:
    """Return the value at *path* (dot-separated) or raise KeyError."""
    parts = path.split(".")
    node: Any = record
    for part in parts:
        if not isinstance(node, dict):
            raise KeyError(path)
        node = node[part]
    return node


class JsonPathFilter:
    """Keep or drop records based on whether a nested field value is in an allowed set."""

    def __init__(
        self,
        field: str,
        values: List[str],
        *,
        invert: bool = False,
        case_sensitive: bool = True,
        missing_ok: bool = False,
    ) -> None:
        field = field.strip()
        if not field:
            raise JsonPathFilterError("field must not be blank")
        if not values:
            raise JsonPathFilterError("at least one value is required")
        self._field = field
        self._case_sensitive = case_sensitive
        if case_sensitive:
            self._values: frozenset = frozenset(values)
        else:
            self._values = frozenset(v.lower() for v in values)
        self._invert = invert
        self._missing_ok = missing_ok

    @property
    def field(self) -> str:
        return self._field

    @property
    def values(self) -> frozenset:
        return self._values

    @property
    def invert(self) -> bool:
        return self._invert

    def matches(self, record: dict) -> bool:
        """Return True if *record* should be kept."""
        try:
            raw = _get_nested(record, self._field)
        except KeyError:
            return self._missing_ok
        candidate = str(raw) if self._case_sensitive else str(raw).lower()
        hit = candidate in self._values
        return (not hit) if self._invert else hit

    def filter(self, records: Iterable[dict]) -> Iterable[dict]:
        """Yield records that pass the filter."""
        for rec in records:
            if self.matches(rec):
                yield rec
