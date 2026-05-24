"""CLI entry-point for the IP filter."""

from __future__ import annotations

import argparse
import json
import sys

from logslice.ip_filter import IPFilter, IPFilterError


def build_ip_filter_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Filter JSON log lines by IP address or CIDR range."
    if parent is not None:
        parser = parent.add_parser("ip-filter", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice-ip-filter", description=description)
    parser.add_argument("--field", required=True, help="Dot-separated field path containing the IP address.")
    parser.add_argument(
        "--network",
        dest="networks",
        action="append",
        required=True,
        metavar="CIDR",
        help="IP address or CIDR to match (repeatable).",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Invert match: drop records that match the given networks.",
    )
    return parser


def run_ip_filter_cli(args: argparse.Namespace, *, stdin=None, stdout=None) -> int:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    try:
        ip_filter = IPFilter(args.field, args.networks, invert=args.invert)
    except IPFilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for raw_line in stdin:
        line = raw_line.rstrip("\n")
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            if ip_filter.keep(record):
                stdout.write(json.dumps(record) + "\n")
        except IPFilterError:
            continue
    return 0


def main() -> None:  # pragma: no cover
    parser = build_ip_filter_parser()
    args = parser.parse_args()
    sys.exit(run_ip_filter_cli(args))


if __name__ == "__main__":  # pragma: no cover
    main()
