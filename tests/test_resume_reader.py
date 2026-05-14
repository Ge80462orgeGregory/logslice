"""Tests for logslice.resume_reader."""

import pytest

from logslice.bookmark import Bookmark
from logslice.resume_reader import ResumeReader


@pytest.fixture()
def bookmark(tmp_path):
    return Bookmark(str(tmp_path / "bm.json"))


def make_log(tmp_path, lines):
    p = tmp_path / "test.log"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


def test_reads_all_lines_from_start(tmp_path, bookmark):
    log = make_log(tmp_path, ['{"a":1}', '{"b":2}'])
    reader = ResumeReader(log, bookmark)
    result = list(reader.lines())
    assert result == ['{"a":1}', '{"b":2}']


def test_second_read_yields_only_new_lines(tmp_path, bookmark):
    log_path = tmp_path / "test.log"
    log_path.write_text('{"a":1}\n', encoding="utf-8")
    reader = ResumeReader(str(log_path), bookmark)
    first = list(reader.lines())
    assert first == ['{"a":1}']

    with log_path.open("a") as fh:
        fh.write('{"b":2}\n')

    second = list(reader.lines())
    assert second == ['{"b":2}']


def test_current_offset_none_before_first_read(tmp_path, bookmark):
    log = make_log(tmp_path, ["line1"])
    reader = ResumeReader(log, bookmark)
    assert reader.current_offset is None


def test_current_offset_updated_after_read(tmp_path, bookmark):
    log = make_log(tmp_path, ["line1", "line2"])
    reader = ResumeReader(log, bookmark)
    list(reader.lines())
    assert reader.current_offset > 0


def test_reset_clears_bookmark(tmp_path, bookmark):
    log = make_log(tmp_path, ["line1"])
    reader = ResumeReader(log, bookmark)
    list(reader.lines())
    assert reader.current_offset is not None
    reader.reset()
    assert reader.current_offset is None


def test_reset_on_unread_file_returns_false(tmp_path, bookmark):
    log = make_log(tmp_path, ["line1"])
    reader = ResumeReader(log, bookmark)
    assert reader.reset() is False


def test_missing_file_raises_os_error(tmp_path, bookmark):
    reader = ResumeReader(str(tmp_path / "ghost.log"), bookmark)
    with pytest.raises(OSError, match="Cannot read"):
        list(reader.lines())
