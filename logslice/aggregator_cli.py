"""CLI sub-command: aggregate field values from a JSON log file."""

import argparse
import json
import sys
from typing import List, Optional

from logslice.aggregator import Aggregator, AggregatorError


def build_aggregator_parser(
    parent: Optional[argparse.ArgumentParser] = None,
) -> argparse.ArgumentParser:
    """Return an ArgumentParser for the *aggregate* sub-command."""
    parser = parent or argparse.ArgumentParser(
        prog="logslice aggregate",
        description="Aggregate field-value counts from JSON log lines.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Path to log file (default: stdin).",
    )
    parser.add_argument(
        "-f",
        "--field",
        dest="fields",
        action="append",
        required=True,
        metavar="FIELD",
        help="Field to aggregate (repeatable).",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Show top-N values per field (default: 10).",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output results as JSON.",
    )
    return parser


def run_aggregator_cli(argv: Optional[List[str]] = None) -> int:
    """Entry point for the aggregate sub-command. Returns exit code."""
    parser = build_aggregator_parser()
    args = parser.parse_args(argv)

    try:
        agg = Aggregator(fields=args.fields)
    except AggregatorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    source = sys.stdin if args.file == "-" else open(args.file)
    try:
        for lineno, raw in enumerate(source, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                print(f"warning: line {lineno} is not valid JSON, skipped.",
                      file=sys.stderr)
                continue
            agg.feed(record)
    finally:
        if source is not sys.stdin:
            source.close()

    if args.output_json:
        print(json.dumps(agg.summary(), indent=2))
    else:
        print(f"Total records: {agg.total}")
        for field in args.fields:
            print(f"\nTop {args.top} values for '{field}':")
            for value, count in agg.top(field, n=args.top):
                print(f"  {value!s:<30} {count}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_aggregator_cli())
