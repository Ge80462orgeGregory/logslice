"""CLI wrapper for the Redactor module."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.redactor import Redactor, RedactorError


def build_redactor_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: E501
    description = "Redact or mask sensitive fields in JSON log lines."
    if parent is not None:
        parser = parent.add_parser("redact", help=description)
    else:
        parser = argparse.ArgumentParser(
            prog="logslice-redact", description=description
        )
    parser.add_argument(
        "-f",
        "--field",
        dest="fields",
        metavar="FIELD",
        action="append",
        default=[],
        help="Dot-separated field path to fully redact (repeatable).",
    )
    parser.add_argument(
        "-m",
        "--mask",
        dest="masks",
        metavar="FIELD=PATTERN",
        action="append",
        default=[],
        help="Mask regex matches inside FIELD value, e.g. email=\\S+@\\S+ (repeatable).",
    )
    parser.add_argument(
        "--placeholder",
        default="***REDACTED***",
        help="Replacement string (default: ***REDACTED***).",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file of JSON lines (default: stdin).",
    )
    return parser


def run_redactor_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_redactor_parser()
    args = parser.parse_args(argv)

    mask_patterns = {}
    for token in args.masks:
        if "=" not in token:
            print(f"error: --mask must be FIELD=PATTERN, got '{token}'", file=sys.stderr)
            return 2
        field, _, pattern = token.partition("=")
        mask_patterns[field] = pattern

    if not args.fields and not mask_patterns:
        print("error: at least one --field or --mask is required.", file=sys.stderr)
        return 2

    try:
        redactor = Redactor(
            fields=args.fields,
            mask_patterns=mask_patterns or None,
            placeholder=args.placeholder,
        )
    except RedactorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    fh = sys.stdin if args.file == "-" else open(args.file)
    try:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(line)
                continue
            print(json.dumps(redactor.redact(record)))
    finally:
        if fh is not sys.stdin:
            fh.close()
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_redactor_cli())


if __name__ == "__main__":  # pragma: no cover
    main()
