"""ResumeReader: reads a log file from a bookmarked offset, updating it as lines are consumed."""

from __future__ import annotations

from typing import Iterator, Optional

from logslice.bookmark import Bookmark


class ResumeReader:
    """Reads *log_path* starting from the last bookmarked position.

    Each call to :meth:`lines` yields decoded lines and advances the
    bookmark so subsequent runs continue from where the last left off.
    """

    def __init__(self, log_path: str, bookmark: Bookmark) -> None:
        self._log_path = log_path
        self._bookmark = bookmark

    @property
    def current_offset(self) -> Optional[int]:
        """Return the stored offset for the managed log file."""
        return self._bookmark.get(self._log_path)

    def lines(self) -> Iterator[str]:
        """Yield lines from the bookmarked offset and persist the new position."""
        offset = self._bookmark.get(self._log_path) or 0
        try:
            with open(self._log_path, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(offset)
                for raw in fh:
                    yield raw.rstrip("\n")
                new_offset = fh.tell()
        except OSError as exc:
            raise OSError(f"Cannot read {self._log_path!r}: {exc}") from exc
        self._bookmark.set(self._log_path, new_offset)

    def reset(self) -> bool:
        """Clear the bookmark so the next :meth:`lines` call starts from the beginning."""
        return self._bookmark.clear(self._log_path)
