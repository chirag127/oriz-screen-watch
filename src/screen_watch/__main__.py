"""CLI: python -m screen_watch [--no-notify] [-v]"""

from __future__ import annotations

import argparse
import sys

from .pipeline import run
from .util import configure_logging, log


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="screen_watch",
                                description="screener.in fundamentals + value-score tracker")
    p.add_argument("--no-notify", action="store_true", help="skip Telegram")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    configure_logging(args.verbose)
    try:
        summary = run(with_notify=not args.no_notify)
    except Exception as e:  # noqa: BLE001
        log.error("run failed: %s", e)
        return 1
    log.info("done: scored=%d new_top=%s notified=%s",
             summary.get("scored", 0), summary.get("new_top"), summary.get("notified"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
