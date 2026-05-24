"""Filter records based on the Shannon entropy of a string field."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Dict, Optional


class EntropyFilterError(Exception):
    """Raised for invalid EntropyFilter configuration."""


def _get_nested(record: Dict[str, Any], field: str) -> Any:
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


class EntropyFilter:
    """Keep or drop records whose field entropy falls within [min_entropy, max_entropy]."""

    def __init__(
        self,
        field: str,
        min_entropy: Optional[float] = None,
        max_entropy: Optional[float] = None,
        invert: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise EntropyFilterError("field must be a non-empty string")
        if min_entropy is None and max_entropy is None:
            raise EntropyFilterError("at least one of min_entropy or max_entropy must be set")
        if min_entropy is not None and min_entropy < 0:
            raise EntropyFilterError("min_entropy must be >= 0")
        if max_entropy is not None and max_entropy < 0:
            raise EntropyFilterError("max_entropy must be >= 0")
        if min_entropy is not None and max_entropy is not None and min_entropy > max_entropy:
            raise EntropyFilterError("min_entropy must be <= max_entropy")
        self._field = field.strip()
        self._min = min_entropy
        self._max = max_entropy
        self._invert = invert

    @property
    def field(self) -> str:
        return self._field

    @property
    def min_entropy(self) -> Optional[float]:
        return self._min

    @property
    def max_entropy(self) -> Optional[float]:
        return self._max

    @property
    def invert(self) -> bool:
        return self._invert

    def matches(self, record: Dict[str, Any]) -> bool:
        if not isinstance(record, dict):
            raise EntropyFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if not isinstance(value, str):
            return False
        entropy = _shannon_entropy(value)
        in_range = True
        if self._min is not None and entropy < self._min:
            in_range = False
        if self._max is not None and entropy > self._max:
            in_range = False
        return (not in_range) if self._invert else in_range
