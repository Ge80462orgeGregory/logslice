"""CLI entry-point for the histogram sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.histogram import Histogram, HistogramError


def build_histogram_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description="Bucket a numeric field and display an ASCII histogram.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    if parent is not None:
        parser = parent.add_parser("histogram", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="logslice histogram", **kwargs)
    parser.add_argument("field", help="Dot-separated field path to bucket (must be numeric).")
    parser.add_argument(
        "--bucket-size",
        type=float,
        default=1.0,
        metavar="N",
        help="Width of each bucket (default: 1.0).",
    )
    parser.add_argument(
        "--bar-width",
        type=int,
        default=40,
        metavar="W",
        help="Maximum bar width in characters (default: 40).",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        default="-",
        help="Input file of newline-delimited JSON (default: stdin).",
    )
    return parser


def run_histogram_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_histogram_parser()
    args = parser.parse_args(argv)

    try:
        hist = Histogram(field=args.field, bucket_size=args.bucket_size)
    except HistogramError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    src = sys.stdin if args.input == "-" else open(args.input)
    try:
        for raw in src:
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                hist.feed(record)
    finally:
        if src is not sys.stdin:
            src.close()

    print(hist.render(bar_width=args.bar_width))
    print(f"\ntotal: {hist.total}  skipped: {hist.skipped}")
    return 0


def main() -> None:
    sys.exit(run_histogram_cli())


if __name__ == "__main__":
    main()
