"""Plays the croak sound whenever the frog says something.

On Windows this uses the built-in multimedia API (winmm), which can play MP3.
On other systems the frog simply stays silent.
"""

from __future__ import annotations

import ctypes
import logging
import sys
from collections.abc import Callable
from pathlib import Path

log = logging.getLogger(__name__)

ALIAS = "frogsound"

MciCommand = Callable[[str], int]


def _send_mci(command: str) -> int:
    """Send an MCI command to Windows. Returns 0 on success."""
    return ctypes.windll.winmm.mciSendStringW(command, None, 0, None)


class Sound:
    def __init__(
        self,
        file: Path,
        duration_ms: int,
        enabled: bool = True,
        mci: MciCommand | None = None,
    ):
        self.file = Path(file)
        self.duration_ms = duration_ms
        self.enabled = enabled
        self._mci = mci or (_send_mci if sys.platform == "win32" else None)
        self._loaded = False
        self._broken = False  # After one failure, stop retrying

    def play(self) -> None:
        if not self.enabled or self._broken or self._mci is None:
            return
        if not self._loaded and not self._load():
            return
        # Only the beginning, otherwise every quip would croak for seconds.
        if self._mci(f"play {ALIAS} from 0 to {self.duration_ms}") != 0:
            self._fail("Could not play the sound.")

    def close(self) -> None:
        if self._loaded:
            self._mci(f"close {ALIAS}")
            self._loaded = False

    def _load(self) -> bool:
        if not self.file.is_file():
            self._fail(f"Sound file is missing: {self.file}")
            return False
        if self._mci(f'open "{self.file}" type mpegvideo alias {ALIAS}') != 0:
            self._fail(f"Could not open the sound file: {self.file}")
            return False
        self._mci(f"set {ALIAS} time format milliseconds")
        self._loaded = True
        return True

    def _fail(self, message: str) -> None:
        log.warning(message)
        self._broken = True
