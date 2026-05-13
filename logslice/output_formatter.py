"""Output formatting for logslice — supports pretty-print, compact JSON, and plain text."""

import json
from typing import Any, Dict, Optional


FORMAT_PRETTY = "pretty"
FORMAT_COMPACT = "compact"
FORMAT_PLAIN = "plain"

SUPPORTED_FORMATS = (FORMAT_PRETTY, FORMAT_COMPACT, FORMAT_PLAIN)


class FormatterError(Exception):
    """Raised when an unsupported format is requested."""


class OutputFormatter:
    """Formats parsed log records for terminal output."""

    def __init__(
        self,
        fmt: str = FORMAT_PRETTY,
        indent: int = 2,
        fields: Optional[list] = None,
        colorize: bool = False,
    ) -> None:
        if fmt not in SUPPORTED_FORMATS:
            raise FormatterError(
                f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}"
            )
        self.fmt = fmt
        self.indent = indent
        self.fields = fields  # if set, only include these top-level keys
        self.colorize = colorize

    def _project(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Return only the requested fields, or the full record."""
        if not self.fields:
            return record
        return {k: record[k] for k in self.fields if k in record}

    def _colorize_json(self, text: str) -> str:
        """Very lightweight ANSI colorization for JSON keys."""
        import re

        # Color keys cyan, string values green
        text = re.sub(r'("[^"]+")(:)', r"\033[36m\1\033[0m\2", text)
        text = re.sub(r'(:\s*)("[^"]*")', r"\1\033[32m\2\033[0m", text)
        return text

    def format(self, record: Dict[str, Any]) -> str:
        """Format a single log record dict into a string."""
        projected = self._project(record)

        if self.fmt == FORMAT_PRETTY:
            output = json.dumps(projected, indent=self.indent, ensure_ascii=False)
            if self.colorize:
                output = self._colorize_json(output)
            return output

        if self.fmt == FORMAT_COMPACT:
            return json.dumps(projected, separators=(",", ":"), ensure_ascii=False)

        # FORMAT_PLAIN: key=value pairs on one line
        parts = [f"{k}={v}" for k, v in projected.items()]
        return "  ".join(parts)

    def format_lines(self, records):
        """Yield formatted strings for an iterable of record dicts."""
        for record in records:
            yield self.format(record)
