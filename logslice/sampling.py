"""Log record sampler — keep every Nth record or a random fraction."""

from __future__ import annotations

import random
from typing import Iterable, Iterator


class SamplingError(Exception):
    """Raised when sampler configuration is invalid."""


class Sampler:
    """Emit a deterministic or random subset of records.

    Parameters
    ----------
    every_n:
        Keep every *n*-th record (1-based counter).  Mutually exclusive
        with *fraction*.
    fraction:
        Keep each record with this probability (0 < fraction <= 1.0).
        Mutually exclusive with *every_n*.
    seed:
        Optional RNG seed for reproducible random sampling.
    """

    def __init__(
        self,
        *,
        every_n: int | None = None,
        fraction: float | None = None,
        seed: int | None = None,
    ) -> None:
        if every_n is not None and fraction is not None:
            raise SamplingError("Specify either 'every_n' or 'fraction', not both.")
        if every_n is None and fraction is None:
            raise SamplingError("One of 'every_n' or 'fraction' must be provided.")
        if every_n is not None and every_n < 1:
            raise SamplingError(f"'every_n' must be >= 1, got {every_n}.")
        if fraction is not None and not (0 < fraction <= 1.0):
            raise SamplingError(f"'fraction' must be in (0, 1], got {fraction}.")

        self._every_n = every_n
        self._fraction = fraction
        self._rng = random.Random(seed)
        self._counter: int = 0
        self._seen: int = 0
        self._emitted: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def seen(self) -> int:
        """Total records presented to the sampler."""
        return self._seen

    @property
    def emitted(self) -> int:
        """Total records passed through the sampler."""
        return self._emitted

    def keep(self, record: object) -> bool:  # noqa: ARG002
        """Return True if *record* should be kept."""
        self._seen += 1
        result = self._should_keep()
        if result:
            self._emitted += 1
        return result

    def filter(self, records: Iterable[object]) -> Iterator[object]:
        """Yield records that pass the sampling criterion."""
        for record in records:
            if self.keep(record):
                yield record

    def reset(self) -> None:
        """Reset counters and the deterministic position."""
        self._counter = 0
        self._seen = 0
        self._emitted = 0

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _should_keep(self) -> bool:
        if self._every_n is not None:
            self._counter += 1
            if self._counter >= self._every_n:
                self._counter = 0
                return True
            return False
        # fraction mode
        return self._rng.random() < self._fraction  # type: ignore[operator]
