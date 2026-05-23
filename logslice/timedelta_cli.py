"""CLI entry point for timedelta-based log filtering."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.timedelta_filter import TimedeltaFilter, TimedeltaFilterError


def build_timedelta_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-timedelta",
        description="Filter JSON log lines to only those within a relative time window.",
    )
    p.add_argument(
        "window",
        help="Relative time window, e.g. '5m', '2h', '30s', '1d'.",
    )
    p.add_argument(
        "--field",
        default="timestamp",
        help="JSON field containing the timestamp (default: timestamp).",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any line cannot be decoded as JSON.",
    )
    p.add_argument(
        "infile",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Input file (default: stdin).",
    )
    return p


def run_timedelta_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_timedelta_parser()
    args = parser.parse_args(argv)

    try:
        tf = TimedeltaFilter(window=args.window, field=args.field)
    except TimedeltaFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    bad_lines = 0
    for raw in args.infile:
        raw = raw.rstrip("\n")
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            bad_lines += 1
            if args.strict:
                print(f"error: invalid JSON: {raw!r}", file=sys.stderr)
                return 1
            continue
        if not isinstance(record, dict):
            continue
        if tf.matches(record):
            print(json.dumps(record))

    if args.strict and bad_lines:
        return 1
    return 0


def main() -> None:
    sys.exit(run_timedelta_cli())


if __name__ == "__main__":
    main()
