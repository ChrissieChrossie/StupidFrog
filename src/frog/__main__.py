"""Entry point: `python -m frog` or simply `frog`."""

from __future__ import annotations

import argparse
import logging

from frog.config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="frog", description="Start the desktop frog.")
    parser.add_argument("--debug", action="store_true", help="Show more log messages")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Imported here so the tests can run without tkinter.
    from frog.app import FrogApp

    FrogApp(Settings()).run()


if __name__ == "__main__":
    main()
