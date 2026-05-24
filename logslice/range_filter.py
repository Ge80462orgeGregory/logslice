"""Filter JSON log records where a field value falls within a set of discrete allowed values."""

from __future__ import annotations

from typing import Any, Iterable


class RangeFilterError(Exception):
    """Raised when RangeFilter is misconfigured."""


def _get_nested(record: dict, field: str) -> Any:
    """Retrieve a possibly dot-separated nested field from *record*."""
    parts = field.split(".")
    current: Any = record
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


class RangeFilter:
    """Keep records whose *field* value is one of the allowed *values*.

    Parameters
    ----------
    field:
        Dot-separated path to the field to inspect.
    values:
        Collection of allowed values. At least one must be provided.
    invert:
        When *True* the filter keeps records whose field value is **not**
        in *values* (i.e. an exclusion list).
    case_sensitive:
        Only relevant for string comparisons. Defaults to *True*.
    """

    def __init__(
        self,
        field: str,
        values: Iterable[Any],
        *,
        invert: bool = False,
        case_sensitive: bool = True,
    ) -> None:
        if not field or not field.strip():
            raise RangeFilterError("field must be a non-empty string")
        values_list = list(values)
        if not values_list:
            raise RangeFilterError("at least one value must be provided")
        self._field = field.strip()
        self._invert = invert
        self._case_sensitive = case_sensitive
        if not case_sensitive:
            self._values = {
                v.lower() if isinstance(v, str) else v for v in values_list
            }
        else:
            self._values = set(values_list)

    @property
    def field(self) -> str:
        return self._field

    @property
    def values(self) -> set:
        return set(self._values)

    @property
    def invert(self) -> bool:
        return self._invert

    @property
    def case_sensitive(self) -> bool:
        return self._case_sensitive

    def matches(self, record: dict) -> bool:
        """Return *True* if *record* should be kept."""
        if not isinstance(record, dict):
            raise RangeFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if value is None:
            return False
        cmp = value.lower() if (not self._case_sensitive and isinstance(value, str)) else value
        contained = cmp in self._values
        return (not contained) if self._invert else contained

    def filter(self, records: Iterable[dict]) -> Iterable[dict]:
        """Yield records from *records* that pass the filter."""
        for record in records:
            if self.matches(record):
                yield record
