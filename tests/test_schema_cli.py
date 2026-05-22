"""Tests for logslice.schema_cli."""
import json
import textwrap
from io import StringIO
from unittest import mock

import pytest

from logslice.schema_cli import run_schema_cli


def _run(argv, stdin_lines=None):
    """Run CLI, capturing stdout/stderr. Returns (exit_code, stdout, stderr)."""
    stdin_text = "\n".join(stdin_lines or []) + "\n"
    with mock.patch("sys.stdin", StringIO(stdin_text)), \
         mock.patch("sys.stdout", new_callable=StringIO) as mock_out, \
         mock.patch("sys.stderr", new_callable=StringIO) as mock_err:
        code = run_schema_cli(argv)
    return code, mock_out.getvalue(), mock_err.getvalue()


def _lines(stdout):
    return [json.loads(l) for l in stdout.strip().splitlines() if l]


def test_no_require_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        run_schema_cli([])
    assert exc.value.code != 0


def test_valid_record_passes_through():
    code, out, _ = _run(
        ["--require", "level"],
        stdin_lines=[json.dumps({"level": "info", "msg": "hi"})],
    )
    assert code == 0
    records = _lines(out)
    assert len(records) == 1
    assert records[0]["level"] == "info"


def test_invalid_record_annotated_non_strict():
    code, out, _ = _run(
        ["--require", "level"],
        stdin_lines=[json.dumps({"msg": "no level here"})],
    )
    assert code == 0
    records = _lines(out)
    assert "_schema_errors" in records[0]


def test_invalid_record_dropped_strict():
    code, out, _ = _run(
        ["--require", "level", "--strict"],
        stdin_lines=[json.dumps({"msg": "no level"})],
    )
    assert code == 0
    assert out.strip() == ""


def test_summary_written_to_stderr():
    lines = [
        json.dumps({"level": "info"}),
        json.dumps({"msg": "bad"}),
    ]
    code, _, err = _run(["--require", "level", "--summary"], stdin_lines=lines)
    assert code == 0
    assert "valid=1" in err
    assert "invalid=1" in err


def test_non_json_line_passed_through():
    code, out, _ = _run(
        ["--require", "level"],
        stdin_lines=["this is not json"],
    )
    assert code == 0
    assert "this is not json" in out


def test_type_check_wrong_type_annotated():
    code, out, _ = _run(
        ["--require", "ts", "--type", "ts:float"],
        stdin_lines=[json.dumps({"ts": "not-a-float"})],
    )
    assert code == 0
    records = _lines(out)
    assert "_schema_errors" in records[0]


def test_invalid_type_spec_exits():
    with pytest.raises(SystemExit):
        run_schema_cli(["--require", "level", "--type", "badspec"])
