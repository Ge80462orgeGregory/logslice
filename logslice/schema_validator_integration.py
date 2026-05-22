"""Integration helpers: wire SchemaValidator into a FilterEngine pipeline."""
from __future__ import annotations

import json
from typing import Dict, Iterable, Iterator, List, Optional

from logslice.filter_engine import FilterEngine
from logslice.schema_validator import SchemaValidationError, SchemaValidator


class ValidatedFilterPipeline:
    """Combines schema validation with query filtering.

    Records flow through:
      1. JSON decode
      2. Schema validation  (annotate or drop)
      3. Query filter       (only if record survived validation)

    Parameters
    ----------
    validator:
        A configured :class:`SchemaValidator` instance.
    engine:
        A configured :class:`FilterEngine` instance (may have zero queries,
        in which case all validated records pass through).
    """

    def __init__(
        self,
        validator: SchemaValidator,
        engine: Optional[FilterEngine] = None,
    ) -> None:
        self._validator = validator
        self._engine = engine
        self._decoded = 0
        self._passed = 0

    # ------------------------------------------------------------------
    def process_lines(self, lines: Iterable[str]) -> Iterator[Dict]:
        """Yield processed records from raw JSON lines."""
        for raw in lines:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            self._decoded += 1

            validated = self._validator.validate(record)
            if validated is None:
                continue  # strict-dropped

            if self._engine is not None and not self._engine.matches(validated):
                continue

            self._passed += 1
            yield validated

    def process_many(
        self, records: Iterable[Dict]
    ) -> Iterator[Dict]:
        """Yield processed records from already-decoded dicts."""
        for record in records:
            self._decoded += 1
            validated = self._validator.validate(record)
            if validated is None:
                continue
            if self._engine is not None and not self._engine.matches(validated):
                continue
            self._passed += 1
            yield validated

    # ------------------------------------------------------------------
    @property
    def decoded_count(self) -> int:
        """Total records decoded (or passed in)."""
        return self._decoded

    @property
    def passed_count(self) -> int:
        """Records that survived both validation and filtering."""
        return self._passed

    def summary(self) -> Dict[str, int]:
        return {
            "decoded": self._decoded,
            "valid": self._validator.valid_count,
            "invalid": self._validator.invalid_count,
            "passed": self._passed,
        }
