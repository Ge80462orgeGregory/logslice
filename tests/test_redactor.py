"""Tests for logslice.redactor and logslice.redactor_cli."""

from __future__ import annotations

import json
import textwrap
from io import StringIO

import pytest

from logslice.redactor import REDACT_PLACEHOLDER, Redactor, RedactorError
from logslice.redactor_cli import run_redactor_cli


# ---------------------------------------------------------------------------
# Redactor unit tests
# ---------------------------------------------------------------------------


def test_no_fields_or_patterns_raises():
    with pytest.raises(RedactorError, match="At least one"):
        Redactor()


def test_invalid_regex_raises():
    with pytest.raises(RedactorError, match="Invalid regex"):
        Redactor(mask_patterns={"email": "[unclosed"})


def test_non_dict_record_raises():
    r = Redactor(fields=["password"])
    with pytest.raises(RedactorError, match="Expected dict"):
        r.redact(["not", "a", "dict"])  # type: ignore[arg-type]


def test_full_redact_top_level_field():
    r = Redactor(fields=["password"])
    result = r.redact({"user": "alice", "password": "s3cr3t"})
    assert result["password"] == REDACT_PLACEHOLDER
    assert result["user"] == "alice"


def test_full_redact_does_not_mutate_original():
    r = Redactor(fields=["token"])
    original = {"token": "abc123", "level": "info"}
    r.redact(original)
    assert original["token"] == "abc123"


def test_full_redact_nested_field():
    r = Redactor(fields=["user.ssn"])
    record = {"user": {"name": "Bob", "ssn": "123-45-6789"}, "level": "warn"}
    result = r.redact(record)
    assert result["user"]["ssn"] == REDACT_PLACEHOLDER
    assert result["user"]["name"] == "Bob"


def test_full_redact_missing_field_is_noop():
    r = Redactor(fields=["nonexistent"])
    record = {"msg": "hello"}
    result = r.redact(record)
    assert result == {"msg": "hello"}


def test_mask_pattern_replaces_substring():
    r = Redactor(mask_patterns={"msg": r"\S+@\S+"})
    record = {"msg": "contact user@example.com for help"}
    result = r.redact(record)
    assert "user@example.com" not in result["msg"]
    assert REDACT_PLACEHOLDER in result["msg"]


def test_mask_pattern_non_string_field_skipped():
    r = Redactor(mask_patterns={"count": r"\d+"})
    record = {"count": 42}
    result = r.redact(record)
    # numeric field left unchanged
    assert result["count"] == 42


def test_custom_placeholder():
    r = Redactor(fields=["secret"], placeholder="[HIDDEN]")
    result = r.redact({"secret": "value"})
    assert result["secret"] == "[HIDDEN]"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def _run(argv, stdin_text=""):
    """Run CLI capturing stdout via monkeypatching stdin."""
    import sys
    from unittest.mock import patch

    captured = StringIO()
    with patch("sys.stdin", StringIO(stdin_text)), patch("sys.stdout", captured):
        code = run_redactor_cli(argv)
    return code, captured.getvalue()


def test_cli_no_args_returns_2():
    code = run_redactor_cli([])
    assert code == 2


def test_cli_redacts_field_from_stdin():
    line = json.dumps({"user": "alice", "password": "hunter2"})
    code, out = _run(["-f", "password"], stdin_text=line + "\n")
    assert code == 0
    result = json.loads(out.strip())
    assert result["password"] == REDACT_PLACEHOLDER
    assert result["user"] == "alice"


def test_cli_invalid_mask_format_returns_2():
    code = run_redactor_cli(["--mask", "noequalssign"])
    assert code == 2


def test_cli_non_json_line_passed_through():
    code, out = _run(["-f", "x"], stdin_text="not json\n")
    assert code == 0
    assert out.strip() == "not json"


def test_cli_mask_via_argv():
    line = json.dumps({"msg": "email me@host.com please"})
    code, out = _run(["--mask", r"msg=\S+@\S+"], stdin_text=line + "\n")
    assert code == 0
    result = json.loads(out.strip())
    assert "me@host.com" not in result["msg"]
