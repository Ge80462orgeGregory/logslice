"""Filter JSON log records by substring keyword presence in a specified field."""

from __future__ import annotations

from typing import Any, Optional


class KeywordFilterError(ValueError):
    """Raised when KeywordFilter is misconfigured."""


def _get_nested(record: dict, field: str) -> Any:
    """Retrieve a value from a possibly dot-separated nested field path."""
    parts = field.split(".")
    current: Any = record
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


class KeywordFilter:
    """Keep or drop records based on keyword substring matches in a field.

    Parameters
    ----------
    field:
        Dot-separated path to the field whose string value is inspected.
    keywords:
        One or more substrings to search for.
    match_any:
        If True (default), a record passes when *any* keyword matches.
        If False, *all* keywords must be present.
    case_sensitive:
        Whether the comparison is case-sensitive (default: False).
    invert:
        When True, the filter logic is inverted — matching records are dropped.
    """

    def __init__(
        self,
        field: str,
        keywords: list[str],
        *,
        match_any: bool = True,
        case_sensitive: bool = False,
        invert: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise KeywordFilterError("field must be a non-empty string")
        if not keywords:
            raise KeywordFilterError("at least one keyword must be provided")
        if any(not isinstance(k, str) for k in keywords):
            raise KeywordFilterError("all keywords must be strings")

        self._field = field.strip()
        self._keywords = keywords
        self._match_any = match_any
        self._case_sensitive = case_sensitive
        self._invert = invert

    @property
    def field(self) -> str:
        return self._field

    @property
    def keywords(self) -> list[str]:
        return list(self._keywords)

    @property
    def match_any(self) -> bool:
        return self._match_any

    @property
    def case_sensitive(self) -> bool:
        return self._case_sensitive

    @property
    def invert(self) -> bool:
        return self._invert

    def matches(self, record: dict) -> bool:
        """Return True if *record* satisfies the keyword filter."""
        if not isinstance(record, dict):
            raise KeywordFilterError("record must be a dict")

        value = _get_nested(record, self._field)
        if value is None:
            return False

        text: str = str(value)
        if not self._case_sensitive:
            text = text.lower()
            keywords = [k.lower() for k in self._keywords]
        else:
            keywords = self._keywords

        if self._match_any:
            result = any(k in text for k in keywords)
        else:
            result = all(k in text for k in keywords)

        return result if not self._invert else not result
