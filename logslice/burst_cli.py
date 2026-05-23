"""CLI wrapper for burst detection on JSON log streams."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable

from logslice.burst_detector import BurstDetector, BurstDetectorError


def build_burst_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-burst",
        description="Emit a warning line whenever log volume bursts above a threshold.",
    )
    p.add_argument(
        "--threshold",
        type=int,
        required=True,
        help="Maximum lines allowed within the window before a burst is flagged.",
    )
    p.add_argument(
        "--window",
        type=float,
        default=1.0,
        help="Sliding window size in seconds (default: 1.0).",
    )
    p.add_argument(
        "--warn-field",
        default="_burst_warning",
        help="Field name injected into the burst-warning JSON line.",
    )
    p.add_argument(
        "--passthrough",
        action="store_true",
        help="Emit every input line regardless of burst status.",
    )
    return p


def run_burst_cli(
    args: argparse.Namespace,
    lines: Iterable[str],
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    try:
        detector = BurstDetector(
            threshold=args.threshold,
            window_seconds=args.window,
        )
    except BurstDetectorError as exc:
        err.write(f"burst-detector error: {exc}\n")
        return 2

    import time

    for raw in lines:
        raw = raw.rstrip("\n")
        now = time.monotonic()
        is_burst = detector.record(ts=now)

        if args.passthrough:
            out.write(raw + "\n")

        if is_burst:
            warning = {
                args.warn_field: True,
                "burst_count": detector.burst_count,
                "window_count": detector.current_window_count(ts=now),
                "threshold": detector.threshold,
            }
            out.write(json.dumps(warning) + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_burst_parser()
    args = parser.parse_args()
    sys.exit(run_burst_cli(args, sys.stdin))


if __name__ == "__main__":  # pragma: no cover
    main()
