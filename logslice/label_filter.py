"""Filter JSON log records by matching label/tag fields against allowed sets."""

from __future__ import annotations

from typing import Any, FrozenSet, Iterable, Optional


class LabelFilterError(Exception):
    """Raised when LabelFilter is misconfigured."""


def _get_nested(record: dict, field: str) -> Any:
    """Retrieve a value from a nested dict using dot-notation."""
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


class LabelFilter:
    """Include or exclude records based on the value of a label field.

    Parameters
    ----------
    field:
        Dot-notation field name whose value is checked (e.g. ``"level"``
        or ``"meta.env"``).  The value is coerced to ``str`` before
        comparison.
    include:
        If provided, only records whose field value is in this set pass.
    exclude:
        If provided, records whose field value is in this set are dropped.
    missing_passes:
        When ``True`` (default) a record that lacks *field* is passed
        through unchanged.  Set to ``False`` to drop such records.
    """

    def __init__(
        self,
        field: str,
        *,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
        missing_passes: bool = True,
    ) -> None:
        if not field or not field.strip():
            raise LabelFilterError("field must be a non-empty string")
        if include is None and exclude is None:
            raise LabelFilterError("at least one of 'include' or 'exclude' must be set")

        self._field = field
        self._include: Optional[FrozenSet[str]] = (
            frozenset(include) if include is not None else None
        )
        self._exclude: Optional[FrozenSet[str]] = (
            frozenset(exclude) if exclude is not None else None
        )
        self._missing_passes = missing_passes

    @property
    def field(self) -> str:
        return self._field

    @property
    def include_labels(self) -> Optional[FrozenSet[str]]:
        return self._include

    @property
    def exclude_labels(self) -> Optional[FrozenSet[str]]:
        return self._exclude

    def matches(self, record: dict) -> bool:
        """Return ``True`` if *record* passes the label filter."""
        if not isinstance(record, dict):
            raise LabelFilterError("record must be a dict")

        raw = _get_nested(record, self._field)
        if raw is None:
            return self._missing_passes

        value = str(raw)

        if self._include is not None and value not in self._include:
            return False
        if self._exclude is not None and value in self._exclude:
            return False
        return True

    def filter(self, records: Iterable[dict]) -> Iterable[dict]:
        """Yield only records that pass the label filter."""
        for rec in records:
            if self.matches(rec):
                yield rec
