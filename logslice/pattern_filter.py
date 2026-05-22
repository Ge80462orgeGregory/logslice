"""Pattern-based log line filter supporting regex include/exclude rules."""

import re
from typing import List, Optional


class PatternFilterError(Exception):
    """Raised when PatternFilter is misconfigured."""


class PatternFilter:
    """Filter JSON log records by matching a field value against regex patterns.

    Records are *included* if they match any include pattern (when provided)
    and *excluded* if they match any exclude pattern.
    """

    def __init__(
        self,
        field: str,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        ignore_case: bool = False,
    ) -> None:
        if not field:
            raise PatternFilterError("field must be a non-empty string")
        if not include and not exclude:
            raise PatternFilterError(
                "at least one include or exclude pattern is required"
            )

        self._field = field
        flags = re.IGNORECASE if ignore_case else 0

        try:
            self._include = [re.compile(p, flags) for p in (include or [])]
            self._exclude = [re.compile(p, flags) for p in (exclude or [])]
        except re.error as exc:
            raise PatternFilterError(f"invalid regex pattern: {exc}") from exc

    @property
    def field(self) -> str:
        return self._field

    def _get_value(self, record: dict) -> Optional[str]:
        """Retrieve the field value, supporting dot-notation for nested keys."""
        parts = self._field.split(".")
        node = record
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return str(node) if node is not None else None

    def matches(self, record: dict) -> bool:
        """Return True if *record* should be kept."""
        if not isinstance(record, dict):
            raise PatternFilterError("record must be a dict")

        value = self._get_value(record)
        if value is None:
            # Field absent — exclude from results when include patterns exist
            return not self._include

        if self._exclude and any(p.search(value) for p in self._exclude):
            return False

        if self._include and not any(p.search(value) for p in self._include):
            return False

        return True

    def filter_records(self, records):
        """Yield records that pass the pattern filter."""
        for record in records:
            if self.matches(record):
                yield record
