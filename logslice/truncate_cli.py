"""CLI entry-point for the truncate-field filter."""

from __future__ import annotations

import argparse
import json
import sys

from logslice.truncate_filter import TruncateFilter, TruncateFilterError


def build_truncate_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(
            prog="logslice-truncate",
            description="Truncate a string field in JSON log records.",
        )
    parser.add_argument("--field", required=True, help="Dot-separated field path to truncate")
    parser.add_argument(
        "--max-length",
        type=int,
        required=True,
        dest="max_length",
        help="Maximum number of characters to keep",
    )
    parser.add_argument(
        "--suffix",
        default="",
        help="String appended after truncation (e.g. '…')",
    )
    parser.add_argument(
        "--drop-non-string",
        action="store_true",
        dest="drop_non_string",
        help="Drop records where the field is not a string",
    )
    return parser


def run_truncate_cli(args: argparse.Namespace, lines: list[str], out=None) -> int:
    if out is None:
        out = sys.stdout
    try:
        tf = TruncateFilter(
            field=args.field,
            max_length=args.max_length,
            suffix=args.suffix,
            drop_non_string=args.drop_non_string,
        )
    except TruncateFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for raw in lines:
        raw = raw.rstrip("\n")
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            print(raw, file=out)
            continue
        result = tf.apply(record)
        if result is not None:
            print(json.dumps(result), file=out)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_truncate_parser()
    args = parser.parse_args()
    sys.exit(run_truncate_cli(args, sys.stdin.readlines()))


if __name__ == "__main__":  # pragma: no cover
    main()
