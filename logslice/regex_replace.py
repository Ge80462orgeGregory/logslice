"""Apply regex substitution to string fields in JSON log records."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


class RegexReplaceError(Exception):
    """Raised when RegexReplace is misconfigured or encounters a bad record."""


def _get_nested(record: Dict[str, Any], field: str) -> Optional[Any]:
    """Return value at a dot-separated field path, or None if missing."""
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _set_nested(record: Dict[str, Any], field: str, value: Any) -> None:
    """Set a value at a dot-separated field path, creating dicts as needed."""
    parts = field.split(".")
    cur: Any = record
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


class RegexReplace:
    """Replace occurrences of a regex pattern within a named field."""

    def __init__(
        self,
        field: str,
        pattern: str,
        replacement: str,
        count: int = 0,
    ) -> None:
        if not field or not field.strip():
            raise RegexReplaceError("field must be a non-empty string")
        if not pattern:
            raise RegexReplaceError("pattern must be a non-empty string")
        if count < 0:
            raise RegexReplaceError("count must be >= 0")
        try:
            self._re = re.compile(pattern)
        except re.error as exc:
            raise RegexReplaceError(f"invalid regex pattern: {exc}") from exc
        self._field = field.strip()
        self._replacement = replacement
        self._count = count

    @property
    def field(self) -> str:
        return self._field

    @property
    def pattern(self) -> str:
        return self._re.pattern

    @property
    def replacement(self) -> str:
        return self._replacement

    @property
    def count(self) -> int:
        return self._count

    def apply(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Return a new record with the substitution applied.

        If the target field is absent or not a string the record is returned
        unchanged (a shallow copy is still made so callers always get a new
        dict at the top level).
        """
        if not isinstance(record, dict):
            raise RegexReplaceError("record must be a dict")
        result = dict(record)
        value = _get_nested(result, self._field)
        if not isinstance(value, str):
            return result
        new_value = self._re.sub(self._replacement, value, count=self._count)
        _set_nested(result, self._field, new_value)
        return result
