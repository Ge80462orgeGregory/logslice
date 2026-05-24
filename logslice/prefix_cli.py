"""CLI entry-point for the prefix-filter subcommand."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional, Sequence

from logslice.prefix_filter import PrefixFilter, PrefixFilterError


def build_prefix_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Filter JSON log lines by a field-value prefix."
    if parent is not None:
        parser = parent.add_parser("prefix", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice-prefix", description=description)
    parser.add_argument("--field", required=True, help="Dot-separated field path to inspect.")
    parser.add_argument("--prefix", required=True, help="Prefix string to match.")
    parser.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Keep records that do NOT start with the prefix.",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        default=False,
        help="Perform case-insensitive comparison.",
    )
    return parser


def run_prefix_cli(args: argparse.Namespace, lines: Optional[List[str]] = None) -> int:
    try:
        pf = PrefixFilter(
            field=args.field,
            prefix=args.prefix,
            invert=args.invert,
            case_sensitive=not args.ignore_case,
        )
    except PrefixFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    source = lines if lines is not None else sys.stdin
    kept = 0
    for raw in source:
        raw = raw.rstrip("\n")
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        try:
            if pf.matches(record):
                print(json.dumps(record))
                kept += 1
        except PrefixFilterError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    return 0


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_prefix_parser()
    args = parser.parse_args(argv)
    sys.exit(run_prefix_cli(args))


if __name__ == "__main__":
    main()
