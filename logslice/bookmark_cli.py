"""CLI helpers for inspecting and managing logslice bookmarks."""

import argparse
import sys
from typing import List, Optional

from logslice.bookmark import Bookmark, BookmarkError

DEFAULT_STORE = ".logslice_bookmarks.json"


def build_bookmark_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-bookmark",
        description="Inspect and manage logslice read-position bookmarks.",
    )
    parser.add_argument(
        "--store",
        default=DEFAULT_STORE,
        metavar="PATH",
        help="Path to the bookmark store (default: %(default)s)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all bookmarked files and their offsets")

    clear_p = sub.add_parser("clear", help="Remove the bookmark for a log file")
    clear_p.add_argument("log_file", help="Path to the log file")

    show_p = sub.add_parser("show", help="Show the offset for a specific log file")
    show_p.add_argument("log_file", help="Path to the log file")

    return parser


def run_bookmark_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_bookmark_parser()
    args = parser.parse_args(argv)

    try:
        bm = Bookmark(args.store)
    except BookmarkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.command == "list":
        entries = bm.all()
        if not entries:
            print("No bookmarks stored.")
        else:
            for path, offset in sorted(entries.items()):
                print(f"{path}\t{offset}")
        return 0

    if args.command == "show":
        offset = bm.get(args.log_file)
        if offset is None:
            print(f"No bookmark for {args.log_file!r}")
            return 1
        print(offset)
        return 0

    if args.command == "clear":
        removed = bm.clear(args.log_file)
        if removed:
            print(f"Cleared bookmark for {args.log_file!r}")
        else:
            print(f"No bookmark found for {args.log_file!r}")
        return 0

    return 1  # unreachable


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_bookmark_cli())
