"""Bookmark manager for persisting read positions in log files."""

import json
import os
from pathlib import Path
from typing import Optional


class BookmarkError(Exception):
    """Raised when a bookmark operation fails."""


class Bookmark:
    """Persists and retrieves byte offsets for log files."""

    def __init__(self, store_path: str) -> None:
        self._path = Path(store_path)
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                with self._path.open("r") as fh:
                    self._data = json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                raise BookmarkError(f"Failed to load bookmark store: {exc}") from exc

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("w") as fh:
                json.dump(self._data, fh)
        except OSError as exc:
            raise BookmarkError(f"Failed to save bookmark store: {exc}") from exc

    def get(self, log_path: str) -> Optional[int]:
        """Return the saved offset for *log_path*, or None if not set."""
        return self._data.get(os.path.abspath(log_path))

    def set(self, log_path: str, offset: int) -> None:
        """Persist *offset* for *log_path*."""
        if offset < 0:
            raise BookmarkError(f"Offset must be non-negative, got {offset}")
        self._data[os.path.abspath(log_path)] = offset
        self._save()

    def clear(self, log_path: str) -> bool:
        """Remove the bookmark for *log_path*. Returns True if it existed."""
        key = os.path.abspath(log_path)
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False

    def all(self) -> dict:
        """Return a copy of all stored bookmarks."""
        return dict(self._data)
