"""Filter that truncates string fields to a maximum length."""

from __future__ import annotations

from typing import Any


class TruncateFilterError(Exception):
    """Raised when TruncateFilter is misconfigured."""


def _get_nested(record: dict, field: str) -> Any:
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _set_nested(record: dict, field: str, value: Any) -> None:
    parts = field.split(".")
    cur = record
    for part in parts[:-1]:
        if not isinstance(cur.get(part), dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


class TruncateFilter:
    """Truncates a string field to *max_length* characters.

    Records where the field is missing or not a string are passed through
    unchanged (or dropped if *drop_non_string* is True).
    """

    def __init__(
        self,
        field: str,
        max_length: int,
        suffix: str = "",
        drop_non_string: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise TruncateFilterError("field must be a non-empty string")
        if max_length < 1:
            raise TruncateFilterError("max_length must be at least 1")
        self._field = field.strip()
        self._max_length = max_length
        self._suffix = suffix
        self._drop_non_string = drop_non_string

    @property
    def field(self) -> str:
        return self._field

    @property
    def max_length(self) -> int:
        return self._max_length

    @property
    def suffix(self) -> str:
        return self._suffix

    def apply(self, record: dict) -> dict | None:
        """Return a (possibly modified) copy of *record*, or None to drop it."""
        if not isinstance(record, dict):
            raise TruncateFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if not isinstance(value, str):
            if self._drop_non_string:
                return None
            return dict(record)
        if len(value) <= self._max_length:
            return dict(record)
        result = dict(record)
        truncated = value[: self._max_length] + self._suffix
        _set_nested(result, self._field, truncated)
        return result
