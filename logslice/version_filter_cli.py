"""CLI entry-point for the version_filter module."""
from __future__ import annotations

import argparse
import json
import sys

from logslice.version_filter import VersionFilter, VersionFilterError


def build_version_filter_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-version",
        description="Filter JSON log lines by a semver version field.",
    )
    p.add_argument("--field", required=True, help="Dot-separated field path containing the version")
    p.add_argument("--min", dest="min_ver", default=None, help="Minimum version (inclusive), e.g. 1.2.0")
    p.add_argument("--max", dest="max_ver", default=None, help="Maximum version (inclusive), e.g. 2.0.0")
    p.add_argument("--invert", action="store_true", help="Invert the filter (exclude matching records)")
    return p


def run_version_filter_cli(argv: list[str] | None = None, *, stdin=None, stdout=None) -> int:
    parser = build_version_filter_parser()
    args = parser.parse_args(argv)
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout

    try:
        vf = VersionFilter(
            field=args.field,
            min_ver=args.min_ver,
            max_ver=args.max_ver,
            invert=args.invert,
        )
    except VersionFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for line in stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        if vf.matches(record):
            print(line, file=stdout)

    return 0


def main() -> None:
    sys.exit(run_version_filter_cli())


if __name__ == "__main__":
    main()
