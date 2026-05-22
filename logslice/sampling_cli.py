"""CLI wrapper for the log sampler."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from logslice.sampling import Sampler, SamplingError


def build_sampling_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Sample JSON log lines — keep every N-th record or a random fraction."
    if parent is not None:
        parser = parent.add_parser("sample", help=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice-sample", description=description)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--every-n",
        type=int,
        metavar="N",
        help="Keep every N-th log line.",
    )
    group.add_argument(
        "--fraction",
        type=float,
        metavar="F",
        help="Keep each line with probability F (0 < F <= 1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible fraction sampling.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print seen/emitted summary to stderr after processing.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    return parser


def run_sampling_cli(args: argparse.Namespace) -> int:
    try:
        sampler = Sampler(
            every_n=args.every_n,
            fraction=args.fraction,
            seed=getattr(args, "seed", None),
        )
    except SamplingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    source = open(args.file) if args.file != "-" else sys.stdin  # noqa: SIM115
    try:
        for raw in source:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if sampler.keep(record):
                print(json.dumps(record))
    finally:
        if args.file != "-":
            source.close()

    if getattr(args, "stats", False):
        print(
            f"sampler: seen={sampler.seen} emitted={sampler.emitted} "
            f"dropped={sampler.seen - sampler.emitted}",
            file=sys.stderr,
        )
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_sampling_parser()
    args = parser.parse_args(argv)
    sys.exit(run_sampling_cli(args))


if __name__ == "__main__":
    main()
