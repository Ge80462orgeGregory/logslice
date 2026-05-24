"""CLI wrapper for CountFilter."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.count_filter import CountFilter, CountFilterError


def build_count_filter_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog or "logslice-count-filter",
        description="Filter JSON log records by occurrence count of a field value.",
    )
    parser.add_argument("--field", required=True, help="Field to track (dot-notation supported)")
    parser.add_argument("--min", type=int, default=None, dest="min_count", help="Minimum occurrence count (inclusive)")
    parser.add_argument("--max", type=int, default=None, dest="max_count", help="Maximum occurrence count (inclusive)")
    parser.add_argument("--invert", action="store_true", help="Invert the filter (drop matching records)")
    return parser


def run_count_filter_cli(argv: Optional[List[str]] = None, *, stdin=None, stdout=None, stderr=None) -> int:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    parser = build_count_filter_parser()
    args = parser.parse_args(argv)

    try:
        cf = CountFilter(
            field=args.field,
            min_count=args.min_count,
            max_count=args.max_count,
            invert=args.invert,
        )
    except CountFilterError as exc:
        stderr.write(f"error: {exc}\n")
        return 2

    for raw in stdin:
        raw = raw.rstrip("\n")
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            stderr.write(f"warning: skipping invalid JSON: {raw!r}\n")
            continue
        try:
            if cf.matches(record):
                stdout.write(json.dumps(record) + "\n")
        except CountFilterError as exc:
            stderr.write(f"warning: {exc}\n")

    return 0


def main() -> None:
    sys.exit(run_count_filter_cli())


if __name__ == "__main__":
    main()
