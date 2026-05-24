"""Filter JSON log records by the value of an environment/string field
matching one of a set of allowed or denied environment names (e.g. prod,
staging, dev)."""

from __future__ import annotations

from typing import Any, Iterable, Iterator


class EnvFilterError(Exception):
    """Raised for invalid EnvFilter configuration."""


def _get_nested(record: dict, field: str) -> Any:
    parts = field.split(".")
    node: Any = record
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


class EnvFilter:
    """Keep or reject records whose *field* value is in *envs*.

    Parameters
    ----------
    field:
        Dot-separated path to the field that holds the environment label.
    envs:
        Collection of environment name strings to match against.
    invert:
        When *True* the filter **drops** records whose field matches *envs*
        and keeps everything else.
    case_sensitive:
        When *False* comparisons are done in lower-case.
    """

    def __init__(
        self,
        field: str,
        envs: Iterable[str],
        *,
        invert: bool = False,
        case_sensitive: bool = True,
    ) -> None:
        if not field or not field.strip():
            raise EnvFilterError("field must be a non-empty string")
        env_list = list(envs)
        if not env_list:
            raise EnvFilterError("at least one environment name is required")
        if any(not isinstance(e, str) or not e.strip() for e in env_list):
            raise EnvFilterError("all environment names must be non-empty strings")
        self._field = field.strip()
        self._case_sensitive = case_sensitive
        if case_sensitive:
            self._envs: frozenset[str] = frozenset(env_list)
        else:
            self._envs = frozenset(e.lower() for e in env_list)
        self._invert = invert

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def envs(self) -> frozenset[str]:
        return self._envs

    @property
    def invert(self) -> bool:
        return self._invert

    @property
    def case_sensitive(self) -> bool:
        return self._case_sensitive

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def matches(self, record: dict) -> bool:
        """Return *True* when *record* should be kept."""
        if not isinstance(record, dict):
            raise EnvFilterError("record must be a dict")
        value = _get_nested(record, self._field)
        if value is None:
            return False
        candidate = str(value) if self._case_sensitive else str(value).lower()
        hit = candidate in self._envs
        return (not hit) if self._invert else hit

    def filter(self, records: Iterable[dict]) -> Iterator[dict]:
        """Yield records that pass the filter."""
        for record in records:
            if self.matches(record):
                yield record
