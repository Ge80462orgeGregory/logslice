"""CLI for flattening nested JSON log records into dot-notation keys."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.field_extractor import flatten_record, FieldExtractorError


def build_flatten_parser(argv: Optional[List[str]] = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-flatten",
        description="Flatten nested JSON log records into dot-notation keys.",
    )
    parser.add_argument(
        "--separator",
        default=".",
        metavar="SEP",
        help="Separator used between key segments (default: '.')",
    )
    parser.add_argument(
        "--prefix",
        default="",
        metavar="PREFIX",
        help="Optional prefix to prepend to every flattened key.",
    )
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Silently skip lines that cannot be parsed or flattened.",
    )
    return parser


def run_flatten_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_flatten_parser()
    args = parser.parse_args(argv)

    for raw in sys.stdin:
        raw = raw.rstrip("\n")
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            if args.skip_invalid:
                continue
            print(f"logslice-flatten: invalid JSON: {exc}", file=sys.stderr)
            return 1

        try:
            flat = flatten_record(record, separator=args.separator, prefix=args.prefix)
        except FieldExtractorError as exc:
            if args.skip_invalid:
                continue
            print(f"logslice-flatten: {exc}", file=sys.stderr)
            return 1

        print(json.dumps(flat))

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_flatten_cli())


if __name__ == "__main__":  # pragma: no cover
    main()
