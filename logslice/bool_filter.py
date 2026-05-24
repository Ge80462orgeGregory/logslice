"""Filter JSON log records by a boolean field value."""

from __future__ import annotations

from typing import Any, Optional


class BoolFilterError(Exception):
    """Raised when BoolFilter is misconfigured."""


def _get_nested(record: dict, field: str) -> Any:
    """Retrieve a possibly dot-separated nested field value."""
    parts = field.split(".")
    node: Any = record
    for part in parts:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


class BoolFilter:
    """Keep or reject records based on a boolean field.

    Parameters
    ----------
    field:
        Dot-separated path to the field to inspect.
    expected:
        ``True`` to keep records where the field is truthy,
        ``False`` to keep records where the field is falsy.
    invert:
        When *True* the sense of *expected* is flipped (convenience flag).
    strict:
        When *True*, records where the field is absent or not a bool are
        rejected; when *False* (default) they are passed through unchanged.
    """

    def __init__(
        self,
        field: str,
        expected: bool = True,
        *,
        invert: bool = False,
        strict: bool = False,
    ) -> None:
        field = field.strip()
        if not field:
            raise BoolFilterError("field must not be empty or blank")
        self._field = field
        self._expected: bool = bool(expected) ^ bool(invert)
        self._strict = strict

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def expected(self) -> bool:
        return self._expected

    @property
    def strict(self) -> bool:
        return self._strict

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def matches(self, record: dict) -> bool:
        """Return *True* if *record* should be kept."""
        if not isinstance(record, dict):
            raise BoolFilterError("record must be a dict")

        value = _get_nested(record, self._field)

        if value is None or not isinstance(value, bool):
            # Field absent or not a proper bool
            return not self._strict

        return value == self._expected

    def filter(self, records: list[dict]) -> list[dict]:
        """Return only records that satisfy :meth:`matches`."""
        return [r for r in records if self.matches(r)]
