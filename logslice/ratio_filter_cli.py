"""CLI entry point for ratio_filter."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.ratio_filter import RatioFilter, RatioFilterError


def build_ratio_filter_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-ratio",
        description="Keep records where numerator/denominator ratio is within bounds.",
    )
    p.add_argument("--numerator", required=True, help="Numerator field (dot-separated path)")
    p.add_argument("--denominator", required=True, help="Denominator field (dot-separated path)")
    p.add_argument("--min", dest="min_val", type=float, default=None, help="Minimum ratio (inclusive)")
    p.add_argument("--max", dest="max_val", type=float, default=None, help="Maximum ratio (inclusive)")
    p.add_argument("--invert", action="store_true", default=False, help="Invert the filter")
    return p


def run_ratio_filter_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_ratio_filter_parser()
    args = parser.parse_args(argv)

    try:
        filt = RatioFilter(
            numerator=args.numerator,
            denominator=args.denominator,
            min_val=args.min_val,
            max_val=args.max_val,
            invert=args.invert,
        )
    except RatioFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for raw in sys.stdin:
        raw = raw.rstrip("\n")
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if filt.matches(record):
            print(raw)

    return 0


def main() -> None:
    sys.exit(run_ratio_filter_cli())


if __name__ == "__main__":
    main()
