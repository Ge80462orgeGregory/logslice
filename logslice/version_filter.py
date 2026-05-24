"""Filter JSON log records by a semver-style version field."""
from __future__ import annotations

import re
from typing import Any, Optional

_VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?$")


class VersionFilterError(Exception):
    """Raised for invalid VersionFilter configuration."""


def _parse_version(v: str) -> tuple[int, ...]:
    m = _VERSION_RE.match(v.strip())
    if not m:
        raise VersionFilterError(f"Invalid version string: {v!r}")
    return tuple(int(x) for x in m.groups(default="0"))


def _get_nested(record: dict, field: str) -> Any:
    parts = field.split(".")
    cur: Any = record
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


class VersionFilter:
    """Keep records whose *field* value falls within [min_ver, max_ver].

    At least one of *min_ver* or *max_ver* must be supplied.
    Comparison is semver-style: major.minor.patch, missing parts default to 0.
    """

    def __init__(
        self,
        field: str,
        min_ver: Optional[str] = None,
        max_ver: Optional[str] = None,
        invert: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise VersionFilterError("field must not be empty")
        if min_ver is None and max_ver is None:
            raise VersionFilterError("At least one of min_ver or max_ver must be set")
        self._field = field.strip()
        self._min = _parse_version(min_ver) if min_ver is not None else None
        self._max = _parse_version(max_ver) if max_ver is not None else None
        if self._min and self._max and self._min > self._max:
            raise VersionFilterError("min_ver must not exceed max_ver")
        self._invert = invert

    @property
    def field(self) -> str:
        return self._field

    @property
    def min_ver(self) -> Optional[tuple[int, ...]]:
        return self._min

    @property
    def max_ver(self) -> Optional[tuple[int, ...]]:
        return self._max

    @property
    def invert(self) -> bool:
        return self._invert

    def matches(self, record: dict) -> bool:
        raw = _get_nested(record, self._field)
        if raw is None:
            return False
        try:
            ver = _parse_version(str(raw))
        except VersionFilterError:
            return False
        result = True
        if self._min is not None and ver < self._min:
            result = False
        if self._max is not None and ver > self._max:
            result = False
        return result if not self._invert else not result
