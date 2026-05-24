"""CLI entry-point for the regex-replace transform."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.regex_replace import RegexReplace, RegexReplaceError


def build_regex_replace_parser(
    parent: Optional[argparse._SubParsersAction] = None,
) -> argparse.ArgumentParser:
    description = "Apply a regex substitution to a field in each JSON log line."
    if parent is not None:
        parser = parent.add_parser("regex-replace", help=description)
    else:
        parser = argparse.ArgumentParser(
            prog="logslice regex-replace", description=description
        )
    parser.add_argument(
        "--field",
        required=True,
        help="Dot-separated field path to apply substitution to.",
    )
    parser.add_argument(
        "--pattern",
        required=True,
        help="Regular-expression pattern to match.",
    )
    parser.add_argument(
        "--replacement",
        default="",
        help="Replacement string (default: empty string).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Maximum substitutions per record; 0 means replace all (default: 0).",
    )
    return parser


def run_regex_replace_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_regex_replace_parser()
    args = parser.parse_args(argv)

    try:
        replacer = RegexReplace(
            field=args.field,
            pattern=args.pattern,
            replacement=args.replacement,
            count=args.count,
        )
    except RegexReplaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for raw in sys.stdin:
        raw = raw.rstrip("\n")
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            print(raw)
            continue
        try:
            result = replacer.apply(record)
        except RegexReplaceError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result))

    return 0


def main() -> None:
    sys.exit(run_regex_replace_cli())


if __name__ == "__main__":
    main()
