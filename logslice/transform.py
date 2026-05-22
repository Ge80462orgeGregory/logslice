"""Field transformation and remapping for JSON log records."""

from typing import Any, Callable, Dict, List, Optional


class TransformError(Exception):
    """Raised when a transformation cannot be applied."""


_TRANSFORMS: Dict[str, Callable[[Any], Any]] = {
    "upper": lambda v: v.upper() if isinstance(v, str) else v,
    "lower": lambda v: v.lower() if isinstance(v, str) else v,
    "str": str,
    "int": int,
    "float": float,
    "bool": lambda v: v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes"),
    "strip": lambda v: v.strip() if isinstance(v, str) else v,
}


def _set_nested(record: dict, dotted_key: str, value: Any) -> None:
    """Set a value in a nested dict using a dot-separated key path."""
    parts = dotted_key.split(".")
    node = record
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def _get_nested(record: dict, dotted_key: str) -> Any:
    """Retrieve a value from a nested dict using a dot-separated key path."""
    parts = dotted_key.split(".")
    node = record
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            raise KeyError(dotted_key)
        node = node[part]
    return node


def apply_rename(record: dict, renames: Dict[str, str]) -> dict:
    """Return a copy of *record* with fields renamed according to *renames* mapping.

    Keys in *renames* are source dot-paths; values are destination dot-paths.
    Missing source fields are silently skipped.
    """
    out = {k: v for k, v in record.items()}
    for src, dst in renames.items():
        try:
            value = _get_nested(record, src)
        except KeyError:
            continue
        _set_nested(out, dst, value)
        # Remove old key if it differs from the destination
        if src != dst and src in out:
            del out[src]
    return out


def apply_transform(record: dict, field: str, transform_name: str) -> dict:
    """Return a copy of *record* with *transform_name* applied to *field*.

    Raises TransformError for unknown transforms or type errors.
    """
    if transform_name not in _TRANSFORMS:
        raise TransformError(
            f"Unknown transform '{transform_name}'. "
            f"Available: {sorted(_TRANSFORMS)}"
        )
    try:
        value = _get_nested(record, field)
    except KeyError:
        return dict(record)  # field absent – return unchanged copy

    fn = _TRANSFORMS[transform_name]
    try:
        new_value = fn(value)
    except (ValueError, TypeError) as exc:
        raise TransformError(
            f"Transform '{transform_name}' failed on field '{field}': {exc}"
        ) from exc

    out = {k: v for k, v in record.items()}
    _set_nested(out, field, new_value)
    return out


def apply_add_field(record: dict, field: str, value: Any) -> dict:
    """Return a copy of *record* with *field* set to *value* (overwrites if present)."""
    out = {k: v for k, v in record.items()}
    _set_nested(out, field, value)
    return out


def apply_drop_fields(record: dict, fields: List[str]) -> dict:
    """Return a copy of *record* with each field in *fields* removed."""
    out = {k: v for k, v in record.items()}
    for field in fields:
        out.pop(field, None)
    return out
