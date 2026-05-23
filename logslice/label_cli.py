"""CLI wrapper for the label/tag filter."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.label_filter import LabelFilter, LabelFilterError


def build_label_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: E501
    description = "Filter JSON log lines by a label/tag field value."
    if parent is not None:
        parser = parent.add_parser("label", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice-label", description=description)

    parser.add_argument("--field", required=True, help="Dot-notation field to inspect (e.g. level).")
    parser.add_argument(
        "--include",
        metavar="LABEL",
        nargs="+",
        help="Only pass records whose field value is one of these labels.",
    )
    parser.add_argument(
        "--exclude",
        metavar="LABEL",
        nargs="+",
        help="Drop records whose field value is one of these labels.",
    )
    parser.add_argument(
        "--drop-missing",
        action="store_true",
        default=False,
        help="Drop records that do not contain the field (default: pass through).",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file of JSON lines (default: stdin).",
    )
    return parser


def run_label_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_label_parser()
    args = parser.parse_args(argv)

    try:
        label_filter = LabelFilter(
            field=args.field,
            include=args.include,
            exclude=args.exclude,
            missing_passes=not args.drop_missing,
        )
    except LabelFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    src = open(args.file) if args.file != "-" else sys.stdin  # noqa: WPS515
    try:
        for raw_line in src:
            raw_line = raw_line.rstrip("\n")
            if not raw_line:
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            try:
                if label_filter.matches(record):
                    print(json.dumps(record))
            except LabelFilterError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
    finally:
        if args.file != "-":
            src.close()

    return 0


def main() -> None:
    sys.exit(run_label_cli())


if __name__ == "__main__":
    main()
