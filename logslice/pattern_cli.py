"""CLI entry-point for the pattern filter."""

import argparse
import json
import sys
from typing import List, Optional

from logslice.pattern_filter import PatternFilter, PatternFilterError


def build_pattern_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-pattern",
        description="Filter JSON log lines by regex patterns on a field value.",
    )
    parser.add_argument("field", help="Field name to match against (dot-notation ok)")
    parser.add_argument(
        "-i",
        "--include",
        metavar="PATTERN",
        action="append",
        dest="include",
        help="Include records whose field matches PATTERN (repeatable)",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        metavar="PATTERN",
        action="append",
        dest="exclude",
        help="Exclude records whose field matches PATTERN (repeatable)",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        default=False,
        help="Case-insensitive matching",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        default="-",
        help="Input file (default: stdin)",
    )
    return parser


def run_pattern_cli(
    args: argparse.Namespace,
    in_stream=None,
    out_stream=None,
    err_stream=None,
) -> int:
    in_stream = in_stream or sys.stdin
    out_stream = out_stream or sys.stdout
    err_stream = err_stream or sys.stderr

    try:
        pf = PatternFilter(
            field=args.field,
            include=args.include,
            exclude=args.exclude,
            ignore_case=args.ignore_case,
        )
    except PatternFilterError as exc:
        err_stream.write(f"error: {exc}\n")
        return 2

    for raw in in_stream:
        raw = raw.rstrip("\n")
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            err_stream.write(f"skipping invalid JSON: {raw!r}\n")
            continue

        try:
            if pf.matches(record):
                out_stream.write(json.dumps(record) + "\n")
        except PatternFilterError as exc:
            err_stream.write(f"error: {exc}\n")
            return 1

    return 0


def main() -> None:  # pragma: no cover
    parser = build_pattern_parser()
    args = parser.parse_args()
    sys.exit(run_pattern_cli(args))


if __name__ == "__main__":  # pragma: no cover
    main()
