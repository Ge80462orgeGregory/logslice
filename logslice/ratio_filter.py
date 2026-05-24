"""Filter records where the ratio of two numeric fields meets a threshold."""

from __future__ import annotations

from typing import Any, Dict, Optional


class RatioFilterError(Exception):
    """Raised for invalid RatioFilter configuration."""


def _get_nested(record: Dict[str, Any], field: str) -> Any:
    parts = field.split(".")
    val: Any = record
    for part in parts:
        if not isinstance(val, dict) or part not in val:
            return None
        val = val[part]
    return val


class RatioFilter:
    """Keep records where numerator/denominator satisfies min/max bounds."""

    def __init__(
        self,
        numerator: str,
        denominator: str,
        *,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        invert: bool = False,
    ) -> None:
        if not numerator or not numerator.strip():
            raise RatioFilterError("numerator field must not be empty")
        if not denominator or not denominator.strip():
            raise RatioFilterError("denominator field must not be empty")
        if min_val is None and max_val is None:
            raise RatioFilterError("at least one of min_val or max_val must be set")
        if min_val is not None and max_val is not None and min_val > max_val:
            raise RatioFilterError("min_val must not exceed max_val")

        self._numerator = numerator.strip()
        self._denominator = denominator.strip()
        self._min_val = min_val
        self._max_val = max_val
        self._invert = invert

    @property
    def numerator(self) -> str:
        return self._numerator

    @property
    def denominator(self) -> str:
        return self._denominator

    @property
    def min_val(self) -> Optional[float]:
        return self._min_val

    @property
    def max_val(self) -> Optional[float]:
        return self._max_val

    @property
    def invert(self) -> bool:
        return self._invert

    def matches(self, record: Dict[str, Any]) -> bool:
        if not isinstance(record, dict):
            return False
        num = _get_nested(record, self._numerator)
        den = _get_nested(record, self._denominator)
        try:
            num_f = float(num)  # type: ignore[arg-type]
            den_f = float(den)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
        if den_f == 0.0:
            return False
        ratio = num_f / den_f
        result = True
        if self._min_val is not None and ratio < self._min_val:
            result = False
        if self._max_val is not None and ratio > self._max_val:
            result = False
        return result if not self._invert else not result
