"""Tests for logslice.output_formatter."""

import json
import pytest

from logslice.output_formatter import (
    OutputFormatter,
    FormatterError,
    FORMAT_PRETTY,
    FORMAT_COMPACT,
    FORMAT_PLAIN,
)

SAMPLE = {"level": "info", "msg": "hello world", "ts": 1700000000, "svc": "api"}


def test_pretty_format_valid_json():
    fmt = OutputFormatter(fmt=FORMAT_PRETTY)
    result = fmt.format(SAMPLE)
    parsed = json.loads(result)
    assert parsed == SAMPLE
    assert "\n" in result  # indented


def test_compact_format_no_whitespace():
    fmt = OutputFormatter(fmt=FORMAT_COMPACT)
    result = fmt.format(SAMPLE)
    assert "\n" not in result
    assert " " not in result
    assert json.loads(result) == SAMPLE


def test_plain_format_key_value_pairs():
    fmt = OutputFormatter(fmt=FORMAT_PLAIN)
    result = fmt.format({"level": "error", "code": 500})
    assert "level=error" in result
    assert "code=500" in result


def test_field_projection():
    fmt = OutputFormatter(fmt=FORMAT_COMPACT, fields=["level", "msg"])
    result = fmt.format(SAMPLE)
    parsed = json.loads(result)
    assert set(parsed.keys()) == {"level", "msg"}
    assert "ts" not in parsed


def test_field_projection_missing_key_skipped():
    fmt = OutputFormatter(fmt=FORMAT_COMPACT, fields=["level", "nonexistent"])
    result = fmt.format(SAMPLE)
    parsed = json.loads(result)
    assert "nonexistent" not in parsed
    assert parsed["level"] == "info"


def test_unsupported_format_raises():
    with pytest.raises(FormatterError, match="Unsupported format"):
        OutputFormatter(fmt="xml")


def test_colorize_adds_ansi_codes():
    fmt = OutputFormatter(fmt=FORMAT_PRETTY, colorize=True)
    result = fmt.format(SAMPLE)
    assert "\033[" in result


def test_format_lines_yields_all():
    fmt = OutputFormatter(fmt=FORMAT_COMPACT)
    records = [{"a": 1}, {"b": 2}, {"c": 3}]
    results = list(fmt.format_lines(records))
    assert len(results) == 3
    assert json.loads(results[0]) == {"a": 1}


def test_empty_record_pretty():
    fmt = OutputFormatter(fmt=FORMAT_PRETTY)
    result = fmt.format({})
    assert json.loads(result) == {}
