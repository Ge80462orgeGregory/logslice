"""Tail watcher module for following log files in real-time."""

import os
import time
import json
from typing import Iterator, Optional


class TailError(Exception):
    """Raised when tailing encounters an unrecoverable error."""


class TailWatcher:
    """Watches a log file and yields new JSON lines as they are appended."""

    def __init__(self, filepath: str, poll_interval: float = 0.2, seek_end: bool = True):
        """
        Args:
            filepath: Path to the log file to watch.
            poll_interval: Seconds between file polls.
            seek_end: If True, start reading from the end of the file.
        """
        self.filepath = filepath
        self.poll_interval = poll_interval
        self.seek_end = seek_end
        self._file = None
        self._inode = None

    def _open(self):
        """Open the file and optionally seek to the end."""
        self._file = open(self.filepath, "r", encoding="utf-8")
        self._inode = os.stat(self.filepath).st_ino
        if self.seek_end:
            self._file.seek(0, 2)

    def _check_rotated(self) -> bool:
        """Return True if the file has been rotated (inode changed or shrunk)."""
        try:
            stat = os.stat(self.filepath)
        except FileNotFoundError:
            return True
        if stat.st_ino != self._inode:
            return True
        if self._file and stat.st_size < self._file.tell():
            return True
        return False

    def follow(self, max_lines: Optional[int] = None) -> Iterator[str]:
        """Yield raw log lines as they appear. Handles log rotation."""
        if not os.path.exists(self.filepath):
            raise TailError(f"File not found: {self.filepath}")

        self._open()
        count = 0
        try:
            while True:
                if self._check_rotated():
                    self._file.close()
                    time.sleep(self.poll_interval)
                    if os.path.exists(self.filepath):
                        self.seek_end = False
                        self._open()
                    continue

                line = self._file.readline()
                if not line:
                    time.sleep(self.poll_interval)
                    continue

                line = line.rstrip("\n")
                if line:
                    yield line
                    count += 1
                    if max_lines is not None and count >= max_lines:
                        return
        finally:
            if self._file:
                self._file.close()

    def follow_json(self, max_lines: Optional[int] = None) -> Iterator[dict]:
        """Yield parsed JSON objects, skipping malformed lines."""
        for raw in self.follow(max_lines=max_lines):
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue
