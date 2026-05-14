"""Command-line entry point for logslice."""

import argparse
import json
import sys

from logslice.filter_engine import FilterEngine
from logslice.output_formatter import OutputFormatter, FormatterError
from logslice.tail_watcher import TailWatcher, TailError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Slice, filter, and tail structured JSON logs.",
    )
    parser.add_argument("file", nargs="?", help="Log file to read (omit for stdin).")
    parser.add_argument("-f", "--follow", action="store_true", help="Follow file for new lines.")
    parser.add_argument("-q", "--query", action="append", dest="queries", default=[],
                        metavar="EXPR", help="Filter expression, e.g. 'level=error'. Repeatable.")
    parser.add_argument("-F", "--fields", help="Comma-separated fields to include in output.")
    parser.add_argument("--format", choices=["pretty", "compact", "plain"], default="compact",
                        dest="fmt", help="Output format (default: compact).")
    parser.add_argument("--color", action="store_true", help="Colorize JSON output.")
    return parser


def process_line(raw: str, engine: FilterEngine, formatter: OutputFormatter,
                 fields: list) -> None:
    """Parse, filter, and print a single log line."""
    try:
        record = json.loads(raw)
    except json.JSONDecodeError:
        return

    if not engine.matches(record):
        return

    try:
        print(formatter.format(record, fields=fields or None))
    except FormatterError:
        pass


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    engine = FilterEngine()
    for q in args.queries:
        try:
            engine.add_query(q)
        except Exception as exc:
            print(f"logslice: invalid query '{q}': {exc}", file=sys.stderr)
            sys.exit(1)

    fields = [f.strip() for f in args.fields.split(",")] if args.fields else []
    formatter = OutputFormatter(fmt=args.fmt, colorize=args.color)

    if args.file and args.follow:
        watcher = TailWatcher(args.file, seek_end=False)
        try:
            for raw in watcher.follow():
                process_line(raw, engine, formatter, fields)
        except TailError as exc:
            print(f"logslice: {exc}", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            pass
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                for raw in fh:
                    process_line(raw.rstrip("\n"), engine, formatter, fields)
        except FileNotFoundError:
            print(f"logslice: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            for raw in sys.stdin:
                process_line(raw.rstrip("\n"), engine, formatter, fields)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
