"""CLI wrapper for record transformation operations."""

import argparse
import json
import sys
from typing import List, Optional

from logslice.transform import (
    TransformError,
    apply_add_field,
    apply_drop_fields,
    apply_rename,
    apply_transform,
)


def build_transform_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-transform",
        description="Apply field transformations to JSON log lines.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    parser.add_argument(
        "--rename",
        metavar="SRC:DST",
        action="append",
        default=[],
        help="Rename field SRC to DST (dot-paths supported). Repeatable.",
    )
    parser.add_argument(
        "--apply",
        metavar="FIELD:TRANSFORM",
        action="append",
        default=[],
        help="Apply named transform to FIELD (e.g. level:upper). Repeatable.",
    )
    parser.add_argument(
        "--add",
        metavar="FIELD=VALUE",
        action="append",
        default=[],
        help="Add or overwrite FIELD with literal VALUE. Repeatable.",
    )
    parser.add_argument(
        "--drop",
        metavar="FIELD",
        action="append",
        default=[],
        help="Drop FIELD from each record. Repeatable.",
    )
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Silently skip lines that are not valid JSON.",
    )
    return parser


def run_transform_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_transform_parser()
    args = parser.parse_args(argv)

    renames = {}
    for spec in args.rename:
        if ":" not in spec:
            print(f"error: --rename expects SRC:DST, got '{spec}'", file=sys.stderr)
            return 2
        src, dst = spec.split(":", 1)
        renames[src] = dst

    transforms = []
    for spec in args.apply:
        if ":" not in spec:
            print(f"error: --apply expects FIELD:TRANSFORM, got '{spec}'", file=sys.stderr)
            return 2
        field, tname = spec.split(":", 1)
        transforms.append((field, tname))

    additions = {}
    for spec in args.add:
        if "=" not in spec:
            print(f"error: --add expects FIELD=VALUE, got '{spec}'", file=sys.stderr)
            return 2
        field, value = spec.split("=", 1)
        additions[field] = value

    src = open(args.file) if args.file != "-" else sys.stdin
    try:
        for raw in src:
            raw = raw.rstrip("\n")
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                if args.skip_invalid:
                    continue
                print(f"error: invalid JSON: {raw!r}", file=sys.stderr)
                return 1

            if not isinstance(record, dict):
                if not args.skip_invalid:
                    print(f"error: expected JSON object, got: {raw!r}", file=sys.stderr)
                    return 1
                continue

            try:
                if renames:
                    record = apply_rename(record, renames)
                for field, tname in transforms:
                    record = apply_transform(record, field, tname)
                for field, value in additions.items():
                    record = apply_add_field(record, field, value)
                if args.drop:
                    record = apply_drop_fields(record, args.drop)
            except TransformError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

            print(json.dumps(record))
    finally:
        if args.file != "-":
            src.close()

    return 0


def main() -> None:
    sys.exit(run_transform_cli())


if __name__ == "__main__":
    main()
