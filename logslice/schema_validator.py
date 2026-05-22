"""Schema validation for JSON log records."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional


class SchemaValidationError(Exception):
    """Raised when schema configuration is invalid."""


class SchemaValidator:
    """Validates JSON log records against a required-field schema.

    Parameters
    ----------
    required_fields:
        Field names (dot-notation supported) that must be present.
    allowed_types:
        Optional mapping of field name -> expected Python type name
        e.g. ``{"level": "str", "ts": "float"}``.
    strict:
        When *True* records that fail validation are dropped; when *False*
        a ``_schema_errors`` key is injected instead.
    """

    _TYPE_MAP: Dict[str, type] = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
    }

    def __init__(
        self,
        required_fields: List[str],
        allowed_types: Optional[Dict[str, str]] = None,
        *,
        strict: bool = False,
    ) -> None:
        if not required_fields:
            raise SchemaValidationError("required_fields must not be empty")
        self._required = required_fields
        self._types: Dict[str, type] = {}
        for field, type_name in (allowed_types or {}).items():
            if type_name not in self._TYPE_MAP:
                raise SchemaValidationError(
                    f"Unknown type '{type_name}' for field '{field}'. "
                    f"Allowed: {sorted(self._TYPE_MAP)}"
                )
            self._types[field] = self._TYPE_MAP[type_name]
        self.strict = strict
        self._valid = 0
        self._invalid = 0

    # ------------------------------------------------------------------
    def _get_nested(self, record: Dict[str, Any], dotted: str) -> Any:
        parts = dotted.split(".")
        obj: Any = record
        for part in parts:
            if not isinstance(obj, dict) or part not in obj:
                raise KeyError(dotted)
            obj = obj[part]
        return obj

    def _errors(self, record: Dict[str, Any]) -> List[str]:
        errs: List[str] = []
        for field in self._required:
            try:
                value = self._get_nested(record, field)
            except KeyError:
                errs.append(f"missing required field '{field}'")
                continue
            if field in self._types and not isinstance(value, self._types[field]):
                expected = self._types[field].__name__
                got = type(value).__name__
                errs.append(f"field '{field}' expected {expected}, got {got}")
        return errs

    def validate(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return validated record, annotated record, or *None* if strict-dropped."""
        if not isinstance(record, dict):
            raise SchemaValidationError("record must be a dict")
        errs = self._errors(record)
        if not errs:
            self._valid += 1
            return record
        self._invalid += 1
        if self.strict:
            return None
        out = dict(record)
        out["_schema_errors"] = errs
        return out

    def validate_many(
        self, records: Iterable[Dict[str, Any]]
    ) -> Iterator[Dict[str, Any]]:
        for rec in records:
            result = self.validate(rec)
            if result is not None:
                yield result

    @property
    def valid_count(self) -> int:
        return self._valid

    @property
    def invalid_count(self) -> int:
        return self._invalid
