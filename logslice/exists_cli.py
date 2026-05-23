"""CLI entry-point for the exists-filter feature."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.exists_filter import ExistsFilter, ExistsFilterError


def build_exists_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: E501
    description = "Keep or drop JSON log records based on field existence."
    if parent is not None:
        parser = parent.add_parser("exists", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice-exists", description=description)

    parser.add_argument("field", help="Dotted field path to check (e.g. 'user.id').")
    parser.add_argument(
        "--allow-null",
        action="store_true",
        default=False,
        help="Accept the field even when its value is null (default: require non-null).",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Invert the filter — drop records where the field exists.",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        default="-",
        help="Input file (default: stdin).",
    )
    return parser


def run_exists_cli(args: argparse.Namespace, lines: Optional[List[str]] = None) -> int:
    try:
        filt = ExistsFilter(
            args.field,
            require_non_null=not args.allow_null,
            invert=args.invert,
        )
    except ExistsFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if lines is None:
        if args.input == "-":
            lines = sys.stdin
        else:
            try:
                lines = open(args.input)  # noqa: WPS515
            except OSError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

    for raw in lines:
        raw = raw.rstrip("\n")
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        try:
            if filt.keep(record):
                print(raw)
        except ExistsFilterError:
            continue

    return 0


def main() -> None:  # pragma: no cover
    parser = build_exists_parser()
    args = parser.parse_args()
    sys.exit(run_exists_cli(args))


if __name__ == "__main__":  # pragma: no cover
    main()
