"""CLI sub-command for deduplicating a stream of JSON log lines."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional, Sequence

from logslice.dedup_filter import DedupError, DedupFilter


def build_dedup_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: SLF001
    description = "Remove duplicate JSON log lines from stdin or a file."
    if parent is not None:
        parser = parent.add_parser("dedup", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice-dedup", description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    parser.add_argument(
        "-f",
        "--fields",
        metavar="FIELD",
        nargs="+",
        default=[],
        help="Dot-separated field(s) used as the dedup key.  Defaults to the whole record.",
    )
    parser.add_argument(
        "-w",
        "--window",
        type=int,
        default=1000,
        metavar="N",
        help="Number of unique keys kept in the sliding window (default: 1000).",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print a summary of processed/dropped lines to stderr when finished.",
    )
    return parser


def run_dedup_cli(args: argparse.Namespace) -> int:
    """Execute the dedup command; returns an exit code."""
    try:
        df = DedupFilter(fields=args.fields or [], window=args.window)
    except DedupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    total = emitted = 0
    source = open(args.file) if args.file != "-" else sys.stdin  # noqa: SIM115
    try:
        for raw in source:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            total += 1
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                # Pass non-JSON lines through unchanged.
                print(raw)
                emitted += 1
                continue
            if not df.is_duplicate(record):
                print(raw)
                emitted += 1
    finally:
        if args.file != "-":
            source.close()

    if args.stats:
        dropped = total - emitted
        print(
            f"dedup: total={total} emitted={emitted} dropped={dropped}",
            file=sys.stderr,
        )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_dedup_parser()
    args = parser.parse_args(argv)
    sys.exit(run_dedup_cli(args))


if __name__ == "__main__":  # pragma: no cover
    main()
