"""Filter JSON log records by whether a string field ends with a given suffix."""

from __future__ import annotations

from typing import Any, Dict, Optional


class SuffixFilterError(Exception):
    """Raised when SuffixFilter is misconfigured."""


def _get_nested(record: Dict[str, Any], field: str) -> Optional[Any]:
    """Retrieve a possibly-nested field using dot notation."""
    parts = field.split(".")
    current: Any = record
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


class SuffixFilter:
    """Keep or drop records based on whether *field* ends with *suffix*.

    Parameters
    ----------
    field:
        Dot-notation path to the string field to inspect.
    suffix:
        The suffix string to match against.
    case_sensitive:
        When *False* (default) the comparison is case-insensitive.
    invert:
        When *True*, keep records that do **not** end with the suffix.
    """

    def __init__(
        self,
        field: str,
        suffix: str,
        *,
        case_sensitive: bool = False,
        invert: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise SuffixFilterError("field must not be empty")
        if suffix is None:
            raise SuffixFilterError("suffix must not be None")
        self._field = field.strip()
        self._suffix = suffix
        self._case_sensitive = case_sensitive
        self._invert = invert

    @property
    def field(self) -> str:
        return self._field

    @property
    def suffix(self) -> str:
        return self._suffix

    @property
    def case_sensitive(self) -> bool:
        return self._case_sensitive

    @property
    def invert(self) -> bool:
        return self._invert

    def matches(self, record: Dict[str, Any]) -> bool:
        """Return *True* if the record should be kept."""
        if not isinstance(record, dict):
            raise SuffixFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if value is None or not isinstance(value, str):
            return False
        haystack = value if self._case_sensitive else value.lower()
        needle = self._suffix if self._case_sensitive else self._suffix.lower()
        result = haystack.endswith(needle)
        return (not result) if self._invert else result
