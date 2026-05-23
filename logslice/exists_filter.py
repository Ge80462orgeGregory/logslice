"""Filter JSON log records based on whether a field exists and/or is non-null."""

from __future__ import annotations

from typing import Any, Dict, Optional


class ExistsFilterError(Exception):
    """Raised when ExistsFilter is misconfigured."""


def _get_nested(record: Dict[str, Any], field: str) -> tuple[bool, Any]:
    """Return (found, value) for a dotted field path."""
    parts = field.split(".")
    current: Any = record
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


class ExistsFilter:
    """Keep or drop records depending on field existence / nullness.

    Parameters
    ----------
    field:
        Dotted path to the field to inspect.
    require_non_null:
        When *True* (default) the field must be present **and** not ``None``.
        When *False* the field only needs to be present (even if ``None``).
    invert:
        When *True* the logic is reversed — records that would normally pass
        are dropped, and vice-versa.
    """

    def __init__(
        self,
        field: str,
        *,
        require_non_null: bool = True,
        invert: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise ExistsFilterError("field must be a non-empty string")
        self._field = field.strip()
        self._require_non_null = require_non_null
        self._invert = invert

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def require_non_null(self) -> bool:
        return self._require_non_null

    @property
    def invert(self) -> bool:
        return self._invert

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def keep(self, record: Dict[str, Any]) -> bool:
        """Return *True* if *record* should be kept."""
        if not isinstance(record, dict):
            raise ExistsFilterError("record must be a dict")
        found, value = _get_nested(record, self._field)
        if self._require_non_null:
            passes = found and value is not None
        else:
            passes = found
        return passes if not self._invert else not passes
