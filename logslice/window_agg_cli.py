"""CLI entry-point for tumbling-window aggregation."""
from __future__ import annotations

import argparse
import json
import sys

from logslice.window_agg import WindowAgg, WindowAggError

_DEFAULT_STATS = ["count", "sum", "min", "max", "mean"]


def build_window_agg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-window-agg",
        description="Bucket a numeric field into tumbling windows and print aggregated stats.",
    )
    p.add_argument("--field", required=True, help="Dot-separated field to aggregate.")
    p.add_argument(
        "--window",
        required=True,
        type=float,
        help="Bucket width (same units as the field value).",
    )
    p.add_argument(
        "--stats",
        nargs="+",
        default=_DEFAULT_STATS,
        metavar="STAT",
        help="Stats to compute: count sum min max mean (default: all).",
    )
    return p


def run_window_agg_cli(
    args: argparse.Namespace,
    lines,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    try:
        agg = WindowAgg(field=args.field, window=args.window, stats=args.stats)
    except WindowAggError as exc:
        err.write(f"error: {exc}\n")
        return 2

    for raw in lines:
        raw = raw.rstrip("\n")
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        try:
            agg.feed(record)
        except WindowAggError:
            continue

    for bucket_start, stats in agg.results():
        row = {"bucket_start": bucket_start, "bucket_end": bucket_start + agg.window}
        row.update(stats)
        out.write(json.dumps(row) + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_window_agg_parser()
    args = parser.parse_args()
    sys.exit(run_window_agg_cli(args, sys.stdin))


if __name__ == "__main__":  # pragma: no cover
    main()
