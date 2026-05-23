"""Filter JSON log records by the presence or absence of null/missing fields."""

from __future__ import annotations

from typing import Any, Iterable


class NullFilterError(ValueError):
    """Raised when NullFilter is misconfigured."""


def _get_nested(record: dict, field: str) -> tuple[bool, Any]:
    """Return (found, value) for a dot-separated field path."""
    parts = field.split(".")
    current: Any = record
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


class NullFilter:
    """Keep or drop records based on whether a field is null or missing.

    Parameters
    ----------
    field:
        Dot-separated field path to inspect.
    drop_null:
        When *True* (default) records where the field is null or missing are
        dropped.  When *False* only records where the field IS null/missing are
        kept (i.e. invert the filter).
    """

    def __init__(self, field: str, *, drop_null: bool = True) -> None:
        if not field or not field.strip():
            raise NullFilterError("field must be a non-empty string")
        self._field = field.strip()
        self._drop_null = drop_null

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def drop_null(self) -> bool:
        return self._drop_null

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _is_null_or_missing(self, record: dict) -> bool:
        found, value = _get_nested(record, self._field)
        return (not found) or (value is None)

    def keep(self, record: Any) -> bool:
        """Return True if *record* should be kept."""
        if not isinstance(record, dict):
            raise NullFilterError("record must be a dict")
        null_or_missing = self._is_null_or_missing(record)
        # drop_null=True  → keep when NOT null/missing
        # drop_null=False → keep when IS  null/missing
        return null_or_missing if not self._drop_null else not null_or_missing

    def filter(self, records: Iterable[Any]) -> Iterable[dict]:
        """Yield records that pass the null filter."""
        for rec in records:
            if self.keep(rec):
                yield rec
