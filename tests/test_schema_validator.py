"""Tests for logslice.schema_validator."""
import pytest

from logslice.schema_validator import SchemaValidationError, SchemaValidator


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_empty_required_raises():
    with pytest.raises(SchemaValidationError, match="required_fields"):
        SchemaValidator([])


def test_unknown_type_raises():
    with pytest.raises(SchemaValidationError, match="Unknown type"):
        SchemaValidator(["level"], allowed_types={"level": "integer"})


def test_valid_construction():
    v = SchemaValidator(["level", "ts"], allowed_types={"ts": "float"})
    assert v.valid_count == 0
    assert v.invalid_count == 0


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------

def test_valid_record_returned_unchanged():
    v = SchemaValidator(["level"])
    rec = {"level": "info", "msg": "hello"}
    result = v.validate(rec)
    assert result == rec
    assert v.valid_count == 1


def test_missing_field_annotated_in_non_strict():
    v = SchemaValidator(["level"])
    result = v.validate({"msg": "oops"})
    assert result is not None
    assert "_schema_errors" in result
    assert any("level" in e for e in result["_schema_errors"])
    assert v.invalid_count == 1


def test_missing_field_dropped_in_strict():
    v = SchemaValidator(["level"], strict=True)
    result = v.validate({"msg": "oops"})
    assert result is None
    assert v.invalid_count == 1


def test_wrong_type_annotated():
    v = SchemaValidator(["ts"], allowed_types={"ts": "float"})
    result = v.validate({"ts": "not-a-float"})
    assert result is not None
    assert "_schema_errors" in result
    assert any("ts" in e for e in result["_schema_errors"])


def test_correct_type_passes():
    v = SchemaValidator(["ts"], allowed_types={"ts": "float"})
    result = v.validate({"ts": 1.23})
    assert "_schema_errors" not in result


def test_non_dict_record_raises():
    v = SchemaValidator(["level"])
    with pytest.raises(SchemaValidationError):
        v.validate(["not", "a", "dict"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Nested field support
# ---------------------------------------------------------------------------

def test_nested_field_present_passes():
    v = SchemaValidator(["meta.env"])
    result = v.validate({"meta": {"env": "prod"}})
    assert result is not None
    assert "_schema_errors" not in result


def test_nested_field_missing_annotated():
    v = SchemaValidator(["meta.env"])
    result = v.validate({"meta": {}})
    assert "_schema_errors" in result
    assert any("meta.env" in e for e in result["_schema_errors"])


# ---------------------------------------------------------------------------
# validate_many()
# ---------------------------------------------------------------------------

def test_validate_many_filters_strict():
    v = SchemaValidator(["level"], strict=True)
    records = [
        {"level": "info"},
        {"msg": "missing level"},
        {"level": "warn"},
    ]
    results = list(v.validate_many(records))
    assert len(results) == 2
    assert v.valid_count == 2
    assert v.invalid_count == 1


def test_validate_many_annotates_non_strict():
    v = SchemaValidator(["level"])
    records = [{"msg": "a"}, {"level": "ok"}]
    results = list(v.validate_many(records))
    assert len(results) == 2
    assert "_schema_errors" in results[0]
    assert "_schema_errors" not in results[1]
