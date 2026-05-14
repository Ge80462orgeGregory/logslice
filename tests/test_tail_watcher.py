"""Tests for the TailWatcher module."""

import json
import os
import tempfile
import threading
import time

import pytest

from logslice.tail_watcher import TailWatcher, TailError


def write_lines(path: str, lines: list, delay: float = 0.05):
    """Helper: append lines to a file with a small delay."""
    def _write():
        time.sleep(delay)
        with open(path, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
                f.flush()
                time.sleep(0.02)
    t = threading.Thread(target=_write, daemon=True)
    t.start()
    return t


def test_tail_error_on_missing_file():
    watcher = TailWatcher("/nonexistent/path/logfile.log")
    with pytest.raises(TailError):
        list(watcher.follow(max_lines=1))


def test_follow_reads_existing_content():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write('{"level": "info"}\n')
        f.write('{"level": "warn"}\n')
        path = f.name

    try:
        watcher = TailWatcher(path, seek_end=False)
        lines = list(watcher.follow(max_lines=2))
        assert len(lines) == 2
        assert '{"level": "info"}' in lines[0]
    finally:
        os.unlink(path)


def test_follow_waits_for_new_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        path = f.name

    try:
        watcher = TailWatcher(path, seek_end=True, poll_interval=0.05)
        write_lines(path, ['{"msg": "hello"}', '{"msg": "world"}'])
        lines = list(watcher.follow(max_lines=2))
        assert len(lines) == 2
        assert '{"msg": "hello"}' in lines[0]
    finally:
        os.unlink(path)


def test_follow_json_parses_objects():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write('{"level": "error", "code": 500}\n')
        f.write('not json at all\n')
        f.write('{"level": "info", "code": 200}\n')
        path = f.name

    try:
        watcher = TailWatcher(path, seek_end=False)
        records = list(watcher.follow_json(max_lines=2))
        assert len(records) == 2
        assert records[0]["level"] == "error"
        assert records[1]["level"] == "info"
    finally:
        os.unlink(path)


def test_follow_json_skips_malformed():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write('garbage line\n')
        f.write('{"ok": true}\n')
        path = f.name

    try:
        watcher = TailWatcher(path, seek_end=False)
        records = list(watcher.follow_json(max_lines=1))
        assert records[0]["ok"] is True
    finally:
        os.unlink(path)
