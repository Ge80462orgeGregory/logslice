"""CLI entry-point for the threshold filter."""

from __future__ import annotations

import argparse
import json
import sys

from logslice.threshold_filter import ThresholdFilter, ThresholdFilterError


def build_threshold_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-threshold",
        description="Keep JSON log lines where a numeric field crosses a threshold.",
    )
    p.add_argument("--field", required=True, help="Dot-separated field path")
    p.add_argument("--threshold", required=True, type=float, help="Boundary value")
    p.add_argument(
        "--direction",
        choices=["above", "below", "equal"],
        default="above",
        help="Comparison direction (default: above)",
    )
    p.add_argument(
        "--exclusive",
        action="store_true",
        help="Use strict comparison (exclude the boundary value itself)",
    )
    p.add_argument(
        "--invert",
        action="store_true",
        help="Invert the filter — keep records that do NOT match",
    )
    return p


def run_threshold_cli(argv: list[str] | None = None) -> int:
    parser = build_threshold_parser()
    args = parser.parse_args(argv)

    try:
        f = ThresholdFilter(
            field=args.field,
            threshold=args.threshold,
            direction=args.direction,
            inclusive=not args.exclusive,
            invert=args.invert,
        )
    except ThresholdFilterError as exc:
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
        try:
            if f.matches(record):
                print(raw)
        except ThresholdFilterError:
            continue
    return 0


def main() -> None:
    sys.exit(run_threshold_cli())


if __name__ == "__main__":
    main()
