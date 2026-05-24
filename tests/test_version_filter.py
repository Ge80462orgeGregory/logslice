"""Tests for logslice.version_filter."""
import pytest
from logslice.version_filter import VersionFilter, VersionFilterError, _parse_version


# --- _parse_version ---

def test_parse_version_full():
    assert _parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_major_minor():
    assert _parse_version("2.5") == (2, 5, 0)


def test_parse_version_major_only():
    assert _parse_version("3") == (3, 0, 0)


def test_parse_version_invalid_raises():
    with pytest.raises(VersionFilterError):
        _parse_version("not-a-version")


# --- VersionFilter construction ---

def test_empty_field_raises():
    with pytest.raises(VersionFilterError):
        VersionFilter(field="", min_ver="1.0.0")


def test_no_bounds_raises():
    with pytest.raises(VersionFilterError):
        VersionFilter(field="version")


def test_min_exceeds_max_raises():
    with pytest.raises(VersionFilterError):
        VersionFilter(field="version", min_ver="2.0.0", max_ver="1.0.0")


def test_invalid_min_raises():
    with pytest.raises(VersionFilterError):
        VersionFilter(field="version", min_ver="bad")


def test_valid_construction():
    vf = VersionFilter(field="version", min_ver="1.0.0", max_ver="2.0.0")
    assert vf.field == "version"
    assert vf.min_ver == (1, 0, 0)
    assert vf.max_ver == (2, 0, 0)
    assert vf.invert is False


# --- matches ---

def test_exact_min_matches():
    vf = VersionFilter(field="v", min_ver="1.0.0")
    assert vf.matches({"v": "1.0.0"}) is True


def test_below_min_excluded():
    vf = VersionFilter(field="v", min_ver="2.0.0")
    assert vf.matches({"v": "1.9.9"}) is False


def test_above_max_excluded():
    vf = VersionFilter(field="v", max_ver="1.5.0")
    assert vf.matches({"v": "1.6.0"}) is False


def test_within_range_matches():
    vf = VersionFilter(field="v", min_ver="1.0.0", max_ver="2.0.0")
    assert vf.matches({"v": "1.8.3"}) is True


def test_missing_field_returns_false():
    vf = VersionFilter(field="v", min_ver="1.0.0")
    assert vf.matches({"other": "1.2.3"}) is False


def test_non_version_value_returns_false():
    vf = VersionFilter(field="v", min_ver="1.0.0")
    assert vf.matches({"v": "not-a-version"}) is False


def test_invert_excludes_matching():
    vf = VersionFilter(field="v", min_ver="1.0.0", max_ver="2.0.0", invert=True)
    assert vf.matches({"v": "1.5.0"}) is False


def test_invert_keeps_non_matching():
    vf = VersionFilter(field="v", min_ver="2.0.0", invert=True)
    assert vf.matches({"v": "1.0.0"}) is True


def test_nested_field_path():
    vf = VersionFilter(field="meta.version", min_ver="3.0.0")
    assert vf.matches({"meta": {"version": "3.1.0"}}) is True
    assert vf.matches({"meta": {"version": "2.9.9"}}) is False
