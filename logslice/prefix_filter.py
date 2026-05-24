"""Filter JSON log records by whether a string field starts with a given prefix."""

from __future__ import annotations

from typing import Any, Optional


class PrefixFilterError(Exception):
    """Raised when PrefixFilter is misconfigured."""


def _get_nested(record: dict, field: str) -> Any:
    """Resolve a dot-separated field path from a dict."""
    parts = field.split(".")
    node: Any = record
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


class PrefixFilter:
    """Keep or drop records based on whether a field value starts with a prefix.

    Parameters
    ----------
    field:
        Dot-separated path to the string field to inspect.
    prefix:
        The string prefix to match against.
    invert:
        When *True* keep records whose field does **not** start with *prefix*.
    case_sensitive:
        When *False* comparison is done in lower-case. Default *True*.
    """

    def __init__(
        self,
        field: str,
        prefix: str,
        *,
        invert: bool = False,
        case_sensitive: bool = True,
    ) -> None:
        if not field or not field.strip():
            raise PrefixFilterError("field must be a non-empty string")
        if prefix is None:
            raise PrefixFilterError("prefix must not be None")
        self._field = field.strip()
        self._prefix = prefix
        self._invert = invert
        self._case_sensitive = case_sensitive

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def invert(self) -> bool:
        return self._invert

    @property
    def case_sensitive(self) -> bool:
        return self._case_sensitive

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def matches(self, record: dict) -> bool:
        """Return *True* if *record* satisfies the prefix condition."""
        if not isinstance(record, dict):
            raise PrefixFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if value is None or not isinstance(value, str):
            return False
        haystack = value if self._case_sensitive else value.lower()
        needle = self._prefix if self._case_sensitive else self._prefix.lower()
        result = haystack.startswith(needle)
        return result if not self._invert else not result
