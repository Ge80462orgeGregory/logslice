"""CLI entry-point for entropy-based field filtering."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.entropy_filter import EntropyFilter, EntropyFilterError


def build_entropy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-entropy",
        description="Filter JSON log lines by the Shannon entropy of a string field.",
    )
    parser.add_argument("--field", required=True, help="Dot-separated field path to evaluate.")
    parser.add_argument("--min", dest="min_entropy", type=float, default=None,
                        help="Minimum entropy (inclusive).")
    parser.add_argument("--max", dest="max_entropy", type=float, default=None,
                        help="Maximum entropy (inclusive).")
    parser.add_argument("--invert", action="store_true",
                        help="Invert the filter — keep records outside the range.")
    return parser


def run_entropy_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_entropy_parser()
    args = parser.parse_args(argv)

    try:
        filt = EntropyFilter(
            field=args.field,
            min_entropy=args.min_entropy,
            max_entropy=args.max_entropy,
            invert=args.invert,
        )
    except EntropyFilterError as exc:
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
            if filt.matches(record):
                print(raw)
        except EntropyFilterError:
            continue

    return 0


def main() -> None:
    sys.exit(run_entropy_cli())


if __name__ == "__main__":
    main()
