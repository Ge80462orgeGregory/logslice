"""Field redaction for sensitive data in JSON log records."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional


REDACT_PLACEHOLDER = "***REDACTED***"


class RedactorError(Exception):
    """Raised when the Redactor is misconfigured."""


class Redactor:
    """Redact or mask values of specified fields in log records.

    Parameters
    ----------
    fields:
        Dot-separated field paths whose values should be fully replaced
        with the placeholder.
    mask_patterns:
        Mapping of field path -> compiled regex.  Matching substrings
        inside the field value are replaced with ``placeholder``.
    placeholder:
        Replacement string used for full redaction (default ``***REDACTED***``).
    """

    def __init__(
        self,
        fields: Optional[Iterable[str]] = None,
        mask_patterns: Optional[Dict[str, str]] = None,
        placeholder: str = REDACT_PLACEHOLDER,
    ) -> None:
        self._fields: List[str] = list(fields or [])
        self._patterns: Dict[str, re.Pattern[str]] = {}
        self._placeholder = placeholder

        if mask_patterns:
            for field, pattern in mask_patterns.items():
                try:
                    self._patterns[field] = re.compile(pattern)
                except re.error as exc:
                    raise RedactorError(
                        f"Invalid regex for field '{field}': {exc}"
                    ) from exc

        if not self._fields and not self._patterns:
            raise RedactorError(
                "At least one field or mask_pattern must be provided."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def redact(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Return a shallow-copied record with sensitive fields redacted."""
        if not isinstance(record, dict):
            raise RedactorError(f"Expected dict, got {type(record).__name__}")
        result = dict(record)
        for field in self._fields:
            self._apply_full(result, field.split("."))
        for field, pattern in self._patterns.items():
            self._apply_mask(result, field.split("."), pattern)
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_full(
        self, record: Dict[str, Any], parts: List[str]
    ) -> None:
        key, *rest = parts
        if key not in record:
            return
        if rest and isinstance(record[key], dict):
            record[key] = dict(record[key])
            self._apply_full(record[key], rest)
        elif not rest:
            record[key] = self._placeholder

    def _apply_mask(
        self, record: Dict[str, Any], parts: List[str], pattern: re.Pattern[str]
    ) -> None:
        key, *rest = parts
        if key not in record:
            return
        if rest and isinstance(record[key], dict):
            record[key] = dict(record[key])
            self._apply_mask(record[key], rest, pattern)
        elif not rest and isinstance(record[key], str):
            record[key] = pattern.sub(self._placeholder, record[key])
