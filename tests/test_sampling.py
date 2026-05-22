"""Tests for logslice.sampling."""

from __future__ import annotations

import pytest

from logslice.sampling import Sampler, SamplingError


# ---------------------------------------------------------------------------
# Construction errors
# ---------------------------------------------------------------------------

def test_both_options_raises():
    with pytest.raises(SamplingError, match="not both"):
        Sampler(every_n=2, fraction=0.5)


def test_no_option_raises():
    with pytest.raises(SamplingError, match="must be provided"):
        Sampler()


def test_every_n_zero_raises():
    with pytest.raises(SamplingError, match=">= 1"):
        Sampler(every_n=0)


def test_fraction_zero_raises():
    with pytest.raises(SamplingError, match="\(0, 1\]"):
        Sampler(fraction=0.0)


def test_fraction_above_one_raises():
    with pytest.raises(SamplingError, match="\(0, 1\]"):
        Sampler(fraction=1.1)


# ---------------------------------------------------------------------------
# every_n mode
# ---------------------------------------------------------------------------

def test_every_1_keeps_all():
    sampler = Sampler(every_n=1)
    records = [{"i": i} for i in range(5)]
    result = list(sampler.filter(records))
    assert result == records


def test_every_2_keeps_half():
    sampler = Sampler(every_n=2)
    records = list(range(10))
    kept = list(sampler.filter(records))
    assert kept == [1, 3, 5, 7, 9]


def test_every_3_correct_indices():
    sampler = Sampler(every_n=3)
    records = list(range(9))
    kept = list(sampler.filter(records))
    assert kept == [2, 5, 8]


def test_seen_and_emitted_counters_every_n():
    sampler = Sampler(every_n=2)
    list(sampler.filter(range(10)))
    assert sampler.seen == 10
    assert sampler.emitted == 5


# ---------------------------------------------------------------------------
# fraction mode
# ---------------------------------------------------------------------------

def test_fraction_one_keeps_all():
    sampler = Sampler(fraction=1.0, seed=0)
    records = list(range(20))
    assert list(sampler.filter(records)) == records


def test_fraction_reproducible_with_seed():
    records = list(range(100))
    run1 = list(Sampler(fraction=0.3, seed=42).filter(records))
    run2 = list(Sampler(fraction=0.3, seed=42).filter(records))
    assert run1 == run2


def test_fraction_different_seeds_differ():
    records = list(range(200))
    run1 = list(Sampler(fraction=0.5, seed=1).filter(records))
    run2 = list(Sampler(fraction=0.5, seed=2).filter(records))
    assert run1 != run2


def test_seen_and_emitted_counters_fraction():
    sampler = Sampler(fraction=1.0, seed=0)
    list(sampler.filter(range(7)))
    assert sampler.seen == 7
    assert sampler.emitted == 7


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

def test_reset_clears_counters():
    sampler = Sampler(every_n=2)
    list(sampler.filter(range(10)))
    sampler.reset()
    assert sampler.seen == 0
    assert sampler.emitted == 0


def test_reset_restarts_every_n_sequence():
    sampler = Sampler(every_n=3)
    first = list(sampler.filter(range(6)))
    sampler.reset()
    second = list(sampler.filter(range(6)))
    assert first == second
