"""CLI entry-point for the json-path-filter command."""
from __future__ import annotations

import argparse
import json
import sys

from logslice.json_path_filter import JsonPathFilter, JsonPathFilterError


def build_json_path_filter_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-json-path-filter",
        description="Keep or drop JSON log lines whose nested field matches one of the given values.",
    )
    p.add_argument("--field", required=True, help="Dot-separated field path, e.g. 'meta.env'")
    p.add_argument(
        "--values",
        required=True,
        nargs="+",
        metavar="VALUE",
        help="One or more values to match against.",
    )
    p.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Invert the match: drop records that match.",
    )
    p.add_argument(
        "--ignore-case",
        action="store_true",
        default=False,
        help="Compare values case-insensitively.",
    )
    p.add_argument(
        "--missing-ok",
        action="store_true",
        default=False,
        help="Keep records where the field is absent (default: drop them).",
    )
    return p


def run_json_path_filter_cli(argv: list[str] | None = None) -> int:
    parser = build_json_path_filter_parser()
    args = parser.parse_args(argv)

    try:
        flt = JsonPathFilter(
            field=args.field,
            values=args.values,
            invert=args.invert,
            case_sensitive=not args.ignore_case,
            missing_ok=args.missing_ok,
        )
    except JsonPathFilterError as exc:
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
        if not isinstance(record, dict):
            continue
        if flt.matches(record):
            print(json.dumps(record))
    return 0


def main() -> None:
    sys.exit(run_json_path_filter_cli())


if __name__ == "__main__":
    main()
