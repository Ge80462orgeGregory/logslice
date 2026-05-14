"""Utility for extracting and flattening fields from parsed JSON log records."""

from typing import Any, Dict, Iterator, List, Optional, Tuple


class FieldExtractorError(Exception):
    """Raised when field extraction encounters an unrecoverable error."""


def _flatten(
    obj: Any,
    prefix: str = "",
    separator: str = ".",
) -> Iterator[Tuple[str, Any]]:
    """Recursively yield (dotted_key, value) pairs from a nested dict."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}{separator}{key}" if prefix else key
            yield from _flatten(value, full_key, separator)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            full_key = f"{prefix}{separator}{index}" if prefix else str(index)
            yield from _flatten(item, full_key, separator)
    else:
        yield prefix, obj


def flatten_record(record: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Return a flat dict of dotted keys to scalar values for *record*."""
    if not isinstance(record, dict):
        raise FieldExtractorError(
            f"Expected a dict record, got {type(record).__name__}"
        )
    return dict(_flatten(record, separator=separator))


def extract_field(record: Dict[str, Any], field_path: str) -> Optional[Any]:
    """Return the value at *field_path* (dot-separated) or None if absent."""
    parts = field_path.split(".")
    current: Any = record
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def extract_fields(
    record: Dict[str, Any], field_paths: List[str]
) -> Dict[str, Any]:
    """Return a dict mapping each requested field path to its extracted value.

    Fields that are absent in *record* are omitted from the result.
    """
    result: Dict[str, Any] = {}
    for path in field_paths:
        value = extract_field(record, path)
        if value is not None:
            result[path] = value
    return result
