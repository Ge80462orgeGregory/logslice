"""Filter JSON log records by whether a string field matches a given case style."""
from __future__ import annotations

import re
from typing import Any, Optional


class CaseFilterError(Exception):
    """Raised when CaseFilter is misconfigured."""


VALID_STYLES = ("upper", "lower", "title", "snake", "camel")

_SNAKE_RE = re.compile(r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$')
_CAMEL_RE = re.compile(r'^[a-z][a-zA-Z0-9]*$')


def _get_nested(record: dict, field: str) -> Any:
    parts = field.split(".")
    node: Any = record
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _matches_style(value: str, style: str) -> bool:
    if style == "upper":
        return value == value.upper() and any(c.isalpha() for c in value)
    if style == "lower":
        return value == value.lower() and any(c.isalpha() for c in value)
    if style == "title":
        return value == value.title() and any(c.isalpha() for c in value)
    if style == "snake":
        return bool(_SNAKE_RE.match(value))
    if style == "camel":
        return bool(_CAMEL_RE.match(value))
    return False


class CaseFilter:
    """Keep or drop records based on the case style of a string field."""

    def __init__(
        self,
        field: str,
        style: str,
        invert: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise CaseFilterError("field must be a non-empty string")
        if style not in VALID_STYLES:
            raise CaseFilterError(
                f"style must be one of {VALID_STYLES}, got {style!r}"
            )
        self._field = field.strip()
        self._style = style
        self._invert = invert

    @property
    def field(self) -> str:
        return self._field

    @property
    def style(self) -> str:
        return self._style

    @property
    def invert(self) -> bool:
        return self._invert

    def matches(self, record: dict) -> bool:
        """Return True if the record should be kept."""
        if not isinstance(record, dict):
            raise CaseFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if not isinstance(value, str):
            return False
        result = _matches_style(value, self._style)
        return (not result) if self._invert else result
