"""Type coercion filter: cast field values to a target type in-place."""

from __future__ import annotations

from typing import Any, Dict, List


COERCION_TYPES = {"int", "float", "str", "bool"}


class TypeCoerceError(Exception):
    """Raised when TypeCoercer is misconfigured or coercion fails fatally."""


def _set_nested(record: dict, dotted_key: str, value: Any) -> None:
    keys = dotted_key.split(".")
    node = record
    for k in keys[:-1]:
        if not isinstance(node.get(k), dict):
            return
        node = node[k]
    node[keys[-1]] = value


def _get_nested(record: dict, dotted_key: str) -> Any:
    keys = dotted_key.split(".")
    node: Any = record
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            raise KeyError(dotted_key)
        node = node[k]
    return node


class TypeCoercer:
    """Coerce one or more fields in a JSON record to specified types.

    Parameters
    ----------
    rules:
        Mapping of dotted field path -> target type name
        (one of 'int', 'float', 'str', 'bool').
    skip_errors:
        When True, fields that cannot be coerced are left unchanged.
        When False (default), a TypeCoerceError is raised.
    """

    def __init__(self, rules: Dict[str, str], *, skip_errors: bool = False) -> None:
        if not rules:
            raise TypeCoerceError("rules must not be empty")
        for field, target in rules.items():
            if not field.strip():
                raise TypeCoerceError("field name must not be blank")
            if target not in COERCION_TYPES:
                raise TypeCoerceError(
                    f"unknown type {target!r}; must be one of {sorted(COERCION_TYPES)}"
                )
        self._rules: Dict[str, str] = dict(rules)
        self._skip_errors = skip_errors

    @property
    def rules(self) -> Dict[str, str]:
        return dict(self._rules)

    @property
    def skip_errors(self) -> bool:
        return self._skip_errors

    def coerce(self, record: dict) -> dict:
        """Return a shallow-copied record with coerced fields."""
        if not isinstance(record, dict):
            raise TypeCoerceError("record must be a dict")
        result = dict(record)
        for field, target in self._rules.items():
            try:
                raw = _get_nested(result, field)
            except KeyError:
                continue
            try:
                coerced = _coerce(raw, target)
            except (ValueError, TypeError) as exc:
                if self._skip_errors:
                    continue
                raise TypeCoerceError(
                    f"cannot coerce field {field!r} value {raw!r} to {target}: {exc}"
                ) from exc
            _set_nested(result, field, coerced)
        return result

    def coerce_many(self, records: List[dict]) -> List[dict]:
        return [self.coerce(r) for r in records]


def _coerce(value: Any, target: str) -> Any:
    if target == "int":
        return int(float(value)) if isinstance(value, str) else int(value)
    if target == "float":
        return float(value)
    if target == "str":
        return str(value)
    if target == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ("true", "1", "yes"):
                return True
            if value.lower() in ("false", "0", "no"):
                return False
            raise ValueError(f"cannot interpret {value!r} as bool")
        return bool(value)
    raise TypeCoerceError(f"unhandled target type {target!r}")
