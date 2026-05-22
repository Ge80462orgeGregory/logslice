"""Tests for logslice.transform and logslice.transform_cli."""

import json
import pytest

from logslice.transform import (
    TransformError,
    apply_add_field,
    apply_drop_fields,
    apply_rename,
    apply_transform,
)
from logslice.transform_cli import run_transform_cli


# ---------------------------------------------------------------------------
# apply_rename
# ---------------------------------------------------------------------------

def test_rename_simple_field():
    record = {"msg": "hello", "level": "info"}
    result = apply_rename(record, {"msg": "message"})
    assert result == {"message": "hello", "level": "info"}


def test_rename_missing_field_skipped():
    record = {"level": "info"}
    result = apply_rename(record, {"msg": "message"})
    assert result == {"level": "info"}


def test_rename_does_not_mutate_original():
    record = {"a": 1}
    apply_rename(record, {"a": "b"})
    assert "a" in record


# ---------------------------------------------------------------------------
# apply_transform
# ---------------------------------------------------------------------------

def test_transform_upper():
    record = {"level": "info"}
    result = apply_transform(record, "level", "upper")
    assert result["level"] == "INFO"


def test_transform_lower():
    record = {"level": "ERROR"}
    result = apply_transform(record, "level", "lower")
    assert result["level"] == "error"


def test_transform_int():
    record = {"code": "42"}
    result = apply_transform(record, "code", "int")
    assert result["code"] == 42


def test_transform_float():
    record = {"latency": "1.5"}
    result = apply_transform(record, "latency", "float")
    assert result["latency"] == pytest.approx(1.5)


def test_transform_str():
    record = {"code": 404}
    result = apply_transform(record, "code", "str")
    assert result["code"] == "404"


def test_transform_strip():
    record = {"msg": "  hello  "}
    result = apply_transform(record, "msg", "strip")
    assert result["msg"] == "hello"


def test_transform_unknown_raises():
    with pytest.raises(TransformError, match="Unknown transform"):
        apply_transform({"a": 1}, "a", "nonexistent")


def test_transform_type_error_raises():
    with pytest.raises(TransformError):
        apply_transform({"a": "not_a_number"}, "a", "int")


def test_transform_missing_field_returns_unchanged():
    record = {"x": 1}
    result = apply_transform(record, "missing", "upper")
    assert result == {"x": 1}


def test_transform_does_not_mutate_original():
    record = {"level": "info"}
    apply_transform(record, "level", "upper")
    assert record["level"] == "info"


# ---------------------------------------------------------------------------
# apply_add_field / apply_drop_fields
# ---------------------------------------------------------------------------

def test_add_field_new():
    record = {"a": 1}
    result = apply_add_field(record, "env", "prod")
    assert result["env"] == "prod"
    assert result["a"] == 1


def test_add_field_overwrites_existing():
    record = {"env": "dev"}
    result = apply_add_field(record, "env", "prod")
    assert result["env"] == "prod"


def test_drop_fields_removes_keys():
    record = {"a": 1, "b": 2, "c": 3}
    result = apply_drop_fields(record, ["a", "c"])
    assert result == {"b": 2}


def test_drop_fields_missing_key_ignored():
    record = {"a": 1}
    result = apply_drop_fields(record, ["z"])
    assert result == {"a": 1}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_rename(capsys, tmp_path):
    log = tmp_path / "log.json"
    log.write_text(json.dumps({"msg": "hi", "level": "info"}) + "\n")
    rc = run_transform_cli(["--rename", "msg:message", str(log)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out.strip())
    assert "message" in out and out["message"] == "hi"


def test_cli_apply_transform(capsys, tmp_path):
    log = tmp_path / "log.json"
    log.write_text(json.dumps({"level": "info"}) + "\n")
    rc = run_transform_cli(["--apply", "level:upper", str(log)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out.strip())
    assert out["level"] == "INFO"


def test_cli_drop_field(capsys, tmp_path):
    log = tmp_path / "log.json"
    log.write_text(json.dumps({"a": 1, "secret": "x"}) + "\n")
    rc = run_transform_cli(["--drop", "secret", str(log)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out.strip())
    assert "secret" not in out


def test_cli_add_field(capsys, tmp_path):
    log = tmp_path / "log.json"
    log.write_text(json.dumps({"a": 1}) + "\n")
    rc = run_transform_cli(["--add", "env=production", str(log)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out.strip())
    assert out["env"] == "production"


def test_cli_invalid_json_skip(capsys, tmp_path):
    log = tmp_path / "log.json"
    log.write_text("not json\n" + json.dumps({"ok": True}) + "\n")
    rc = run_transform_cli(["--skip-invalid", str(log)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out.strip())
    assert out["ok"] is True


def test_cli_invalid_json_no_skip_returns_error(tmp_path):
    log = tmp_path / "log.json"
    log.write_text("bad line\n")
    rc = run_transform_cli([str(log)])
    assert rc == 1
