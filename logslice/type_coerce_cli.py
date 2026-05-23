"""CLI wrapper for the type-coercion filter."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.type_coerce import TypeCoerceError, TypeCoercer


def build_type_coerce_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Cast JSON log fields to a target type.",
    )
    parser.add_argument(
        "--field",
        metavar="FIELD:TYPE",
        dest="rules",
        action="append",
        required=True,
        help=(
            "Dotted field path and target type separated by ':'. "
            "Allowed types: int, float, str, bool. "
            "May be specified multiple times."
        ),
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        default=False,
        help="Leave fields unchanged instead of exiting on coercion failure.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    return parser


def _parse_rules(raw_rules: List[str]) -> dict:
    rules: dict = {}
    for token in raw_rules:
        if ":" not in token:
            raise TypeCoerceError(
                f"invalid rule {token!r}: expected FIELD:TYPE format"
            )
        field, _, target = token.partition(":")
        rules[field.strip()] = target.strip()
    return rules


def run_type_coerce_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_type_coerce_parser()
    args = parser.parse_args(argv)

    try:
        rules = _parse_rules(args.rules)
        coercer = TypeCoercer(rules, skip_errors=args.skip_errors)
    except TypeCoerceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    src = sys.stdin if args.input == "-" else open(args.input)
    try:
        for raw in src:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                print(raw)
                continue
            try:
                result = coercer.coerce(record)
            except TypeCoerceError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            print(json.dumps(result))
    finally:
        if src is not sys.stdin:
            src.close()

    return 0


def main() -> None:
    sys.exit(run_type_coerce_cli())


if __name__ == "__main__":
    main()
