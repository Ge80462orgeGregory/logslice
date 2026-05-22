"""CLI entry-point for the join-filter feature."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.join_filter import JoinError, JoinFilter


def build_join_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog or "logslice-join",
        description="Left-join a primary JSON log stream with a right-hand file.",
    )
    parser.add_argument(
        "right_file",
        metavar="RIGHT_FILE",
        help="Path to the right-hand JSON log file used to build the join index.",
    )
    parser.add_argument(
        "--key",
        required=True,
        metavar="FIELD",
        help="Dot-separated field path used as the join key in both streams.",
    )
    parser.add_argument(
        "--prefix",
        default="joined_",
        metavar="PREFIX",
        help="Prefix for fields merged from the right record (default: 'joined_').",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        default=None,
        help="Primary log file to read (default: stdin).",
    )
    return parser


def run_join_cli(argv: Optional[List[str]] = None) -> int:  # noqa: D401
    """Parse *argv*, run the join, return an exit code."""
    parser = build_join_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.right_file, "r", encoding="utf-8") as fh:
            right_lines = fh.readlines()
    except OSError as exc:
        print(f"error: cannot open right file: {exc}", file=sys.stderr)
        return 1

    try:
        jf = JoinFilter(key=args.key, right_lines=right_lines, prefix=args.prefix)
    except JoinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.input:
        try:
            primary = open(args.input, "r", encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot open input file: {exc}", file=sys.stderr)
            return 1
    else:
        primary = sys.stdin

    try:
        for line in jf.process(primary):
            print(line)
    finally:
        if args.input:
            primary.close()

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_join_cli())


if __name__ == "__main__":  # pragma: no cover
    main()
