"""Entry point: `python -m frog` or simply `frog`."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from frog.config import Settings

# The .exe has no console window, so it writes its log to this file instead.
LOG_FILE = Path.home() / ".frog" / "frog.log"


def main() -> None:
    parser = argparse.ArgumentParser(prog="frog", description="Start the desktop frog.")
    parser.add_argument("--debug", action="store_true", help="Show more log messages")
    args = parser.parse_args()

    log_target = {}
    if getattr(sys, "frozen", False):
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        log_target = {"filename": LOG_FILE, "filemode": "w", "encoding": "utf-8"}
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        **log_target,
    )

    try:
        # Imported here so the tests can run without tkinter.
        from frog.app import FrogApp

        FrogApp(Settings()).run()
    except Exception:
        logging.exception("The frog crashed")  # Ends up in the log file for the .exe
        raise


if __name__ == "__main__":
    main()
