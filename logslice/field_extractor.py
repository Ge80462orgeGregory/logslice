"""Utilities for flattening and extracting fields from nested JSON records."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class FieldExtractorError(Exception):
    """Raised when a field extraction operation cannot be completed."""


def _flatten(
    obj: Any,
    parent_key: str,
    separator: str,
    result: Dict[str, Any],
) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{separator}{k}" if parent_key else k
            _flatten(v, new_key, separator, result)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_key = f"{parent_key}{separator}{i}" if parent_key else str(i)
            _flatten(v, new_key, separator, result)
    else:
        result[parent_key] = obj


def flatten_record(
    record: Any,
    separator: str = ".",
    prefix: str = "",
) -> Dict[str, Any]:
    """Return a flat dict with dot-notation keys from a nested dict."""
    if not isinstance(record, dict):
        raise FieldExtractorError(
            f"flatten_record expects a dict, got {type(record).__name__}"
        )
    result: Dict[str, Any] = {}
    _flatten(record, prefix, separator, result)
    # If prefix was given, keys start with "prefix.original" — strip leading sep
    if prefix:
        stripped: Dict[str, Any] = {}
        lead = prefix + separator
        for k, v in result.items():
            stripped[k[len(lead):] if k.startswith(lead) else k] = v
        # Re-add prefix to all keys
        return {f"{prefix}{separator}{k}": v for k, v in stripped.items()}
    return result


def extract_field(record: Dict[str, Any], field: str, separator: str = ".") -> Any:
    """Retrieve a possibly-nested field value using dot notation."""
    parts = field.split(separator)
    current: Any = record
    for part in parts:
        if not isinstance(current, dict):
            raise FieldExtractorError(
                f"Cannot traverse into non-dict at segment '{part}' of field '{field}'"
            )
        if part not in current:
            raise FieldExtractorError(f"Field '{field}' not found in record")
        current = current[part]
    return current


def extract_fields(
    record: Dict[str, Any],
    fields: List[str],
    separator: str = ".",
    skip_missing: bool = False,
) -> Dict[str, Any]:
    """Extract multiple fields, returning a dict of field -> value."""
    out: Dict[str, Any] = {}
    for f in fields:
        try:
            out[f] = extract_field(record, f, separator)
        except FieldExtractorError:
            if not skip_missing:
                raise
    return out
