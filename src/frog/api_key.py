"""Store the Anthropic API key as a user environment variable, like `setx` does.

The key never ends up in the code or in settings.json:
- It is set for the running frog right away (os.environ).
- On Windows it is also saved in HKEY_CURRENT_USER\\Environment,
  so the frog finds it again after a restart.
"""

from __future__ import annotations

import logging
import os
import sys

log = logging.getLogger(__name__)

ENV_NAME = "ANTHROPIC_API_KEY"
KEY_PREFIX = "sk-ant-"


def current() -> str:
    return os.environ.get(ENV_NAME, "")


def looks_valid(key: str) -> bool:
    """A quick sanity check. Claude itself decides whether the key really works."""
    return key.startswith(KEY_PREFIX) and not any(c.isspace() for c in key)


def masked(key: str) -> str:
    """Show only the end of the key, e.g. 'sk-ant-...x7Qa'."""
    return f"{KEY_PREFIX}...{key[-4:]}" if key else ""


def save(key: str) -> bool:
    """Use the key now and remember it for the next start. Returns True if it was remembered."""
    os.environ[ENV_NAME] = key
    return _write_user_env(key)


def remove() -> bool:
    """Forget the key. Returns True if it was also removed for the next start."""
    os.environ.pop(ENV_NAME, None)
    return _write_user_env(None)


def _write_user_env(value: str | None) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
            if value is None:
                try:
                    winreg.DeleteValue(k, ENV_NAME)
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(k, ENV_NAME, 0, winreg.REG_SZ, value)
        _announce_change()
        return True
    except OSError:
        log.exception("Could not save the API key for the next start")
        return False


def _announce_change() -> None:
    """Tell Windows that the environment changed, so new programs see it (like setx)."""
    import ctypes

    hwnd_broadcast, wm_settingchange, smto_abortifhung = 0xFFFF, 0x001A, 0x0002
    ctypes.windll.user32.SendMessageTimeoutW(
        hwnd_broadcast, wm_settingchange, 0, "Environment", smto_abortifhung, 1000, None
    )
