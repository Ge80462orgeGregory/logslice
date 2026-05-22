"""CLI entry-point for schema validation of JSON log streams."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.schema_validator import SchemaValidationError, SchemaValidator


def build_schema_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-schema",
        description="Validate JSON log lines against a required-field schema.",
    )
    p.add_argument(
        "--require",
        metavar="FIELD",
        action="append",
        dest="required",
        default=[],
        help="Required field (dot-notation). Repeatable.",
    )
    p.add_argument(
        "--type",
        metavar="FIELD:TYPE",
        action="append",
        dest="types",
        default=[],
        help="Expected type for a field, e.g. level:str. Repeatable.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Drop invalid records instead of annotating them.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print validation summary to stderr after processing.",
    )
    p.add_argument(
        "file",
        nargs="?",
        help="Input file (default: stdin).",
    )
    return p


def _parse_types(raw: List[str]) -> dict:
    result = {}
    for item in raw:
        if ":" not in item:
            raise SystemExit(f"Invalid --type spec '{item}': expected FIELD:TYPE")
        field, _, type_name = item.partition(":")
        result[field.strip()] = type_name.strip()
    return result


def run_schema_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_schema_parser()
    args = parser.parse_args(argv)

    if not args.required:
        parser.error("At least one --require FIELD must be specified.")

    try:
        allowed_types = _parse_types(args.types)
        validator = SchemaValidator(
            required_fields=args.required,
            allowed_types=allowed_types or None,
            strict=args.strict,
        )
    except SchemaValidationError as exc:
        print(f"schema error: {exc}", file=sys.stderr)
        return 2

    src = open(args.file) if args.file else sys.stdin
    try:
        for raw in src:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                print(raw)  # pass through non-JSON lines unchanged
                continue
            result = validator.validate(record)
            if result is not None:
                print(json.dumps(result))
    finally:
        if args.file:
            src.close()

    if args.summary:
        print(
            f"valid={validator.valid_count} invalid={validator.invalid_count}",
            file=sys.stderr,
        )
    return 0


def main() -> None:
    sys.exit(run_schema_cli())


if __name__ == "__main__":
    main()
