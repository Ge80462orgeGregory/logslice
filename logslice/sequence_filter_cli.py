"""CLI wrapper for SequenceFilter."""
from __future__ import annotations

import argparse
import json
import sys

from logslice.sequence_filter import SequenceFilter, SequenceFilterError


def build_sequence_filter_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-sequence",
        description="Keep only records where a numeric field is monotonically increasing (or decreasing).",
    )
    p.add_argument("--field", required=True, help="Dot-separated field path to inspect.")
    p.add_argument(
        "--decreasing",
        action="store_true",
        default=False,
        help="Require strictly decreasing values instead of increasing.",
    )
    return p


def run_sequence_filter_cli(
    args: argparse.Namespace,
    lines: list[str],
    print_fn=print,
) -> int:
    try:
        sf = SequenceFilter(args.field, decreasing=args.decreasing)
    except SequenceFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        try:
            if sf.keep(record):
                print_fn(json.dumps(record))
        except SequenceFilterError:
            continue
    return 0


def main() -> None:  # pragma: no cover
    parser = build_sequence_filter_parser()
    args = parser.parse_args()
    lines = sys.stdin.readlines()
    sys.exit(run_sequence_filter_cli(args, lines))


if __name__ == "__main__":  # pragma: no cover
    main()
