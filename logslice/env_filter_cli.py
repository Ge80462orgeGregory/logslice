"""CLI wrapper for EnvFilter — filter JSON log lines by environment label."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.env_filter import EnvFilter, EnvFilterError


def build_env_filter_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-env",
        description="Filter JSON log lines by environment field value.",
    )
    parser.add_argument(
        "--field",
        required=True,
        help="Dot-separated field path containing the environment label.",
    )
    parser.add_argument(
        "--envs",
        required=True,
        nargs="+",
        metavar="ENV",
        help="One or more environment names to match (e.g. prod staging).",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Exclude records matching the given environments instead of keeping them.",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        default=False,
        help="Perform case-insensitive comparison.",
    )
    return parser


def run_env_filter_cli(argv: List[str] | None = None, *, stdin=None, stdout=None) -> int:
    parser = build_env_filter_parser()
    args = parser.parse_args(argv)

    _in = stdin or sys.stdin
    _out = stdout or sys.stdout

    try:
        env_filter = EnvFilter(
            field=args.field,
            envs=args.envs,
            invert=args.invert,
            case_sensitive=not args.ignore_case,
        )
    except EnvFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for raw in _in:
        raw = raw.rstrip("\n")
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        try:
            if env_filter.matches(record):
                print(json.dumps(record), file=_out)
        except EnvFilterError:
            continue

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_env_filter_cli())


if __name__ == "__main__":  # pragma: no cover
    main()
