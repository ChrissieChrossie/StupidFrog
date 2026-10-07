"""Quips from Claude, fetched in the background so the frog never has to wait.

How it works:
- The frog keeps a small stock of AI quips.
- When the stock runs low, a background thread fetches new ones.
- If the stock is empty, AI is off, there is no internet or no API key,
  the built-in list is used instead.
"""

from __future__ import annotations

import logging
import os
import queue
import threading
import time
from collections.abc import Callable

from frog.quips import QuipSource

log = logging.getLogger(__name__)

QUIPS_PER_REQUEST = 5
PAUSE_AFTER_ERROR_S = 120.0
MAX_QUIP_CHARS = 90
MAX_PERSONALITY_CHARS = 1000
LOW_STOCK = 2

# Shown to the user in the personality dialog, therefore German.
DEFAULT_PERSONALITY = (
    "Ein kleiner Pixelfrosch, der sich für den Desktop-Manager hält. "
    "Er glaubt, ohne ihn würde dieser Computer sofort im Chaos versinken. "
    "Er ist sehr sarkastisch: Er kommentiert offene Fenster, volle Desktops, "
    "vergessene Downloads und die Arbeitsmoral des Nutzers mit trockenem Spott. "
    "Er spricht wie ein genervter Büro-Chef, der alles besser weiß."
)

# Earlier default personalities. Users who only saved one of these get the current default.
LEGACY_PERSONALITIES = (
    "Ein frecher, kleiner Pixelfrosch, der auf einem Windows-Desktop herumhüpft. "
    "Macht witzige, etwas doofe Kommentare zum Nutzer, zum Computer und zum Froschleben.",
)

# These rules always apply, whatever personality is configured.
BASE_RULES = (
    "Whatever the personality: cheeky and sarcastic is fine, but never mean, "
    "never insulting, nothing indecent. Always write in German, without emojis. "
    "Each quip has at most 12 words."
)


def normalize_personality(personality: str) -> str:
    """Clean up a personality text. An empty result means: use the default."""
    personality = personality.strip()[:MAX_PERSONALITY_CHARS]
    if personality == DEFAULT_PERSONALITY or personality in LEGACY_PERSONALITIES:
        return ""
    return personality


def build_system_prompt(personality: str) -> str:
    """Combine the personality with the fixed rules."""
    personality = normalize_personality(personality) or DEFAULT_PERSONALITY
    return (
        "You are a desktop frog that makes short quips. "
        f"This is your personality:\n{personality}\n\n{BASE_RULES}"
    )


def ai_available() -> tuple[bool, str]:
    """Check whether Claude can be used. Returns (available, reason)."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False, "package 'anthropic' is missing (pip install -e .)"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False, "environment variable ANTHROPIC_API_KEY is not set"
    return True, ""


def parse_quips(text: str) -> list[str]:
    """Turn Claude's reply into a clean list of quips."""
    quips = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*•0123456789.) ").strip().strip('"„“')
        if line and len(line) <= MAX_QUIP_CHARS:
            quips.append(line)
    return quips


def ask_claude(model: str, personality: str = "") -> list[str]:
    """Fetch new quips from Claude. The API key is read from ANTHROPIC_API_KEY."""
    import anthropic

    client = anthropic.Anthropic(timeout=20.0, max_retries=1)
    reply = client.messages.create(
        model=model,
        max_tokens=400,
        system=build_system_prompt(personality),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Give me {QUIPS_PER_REQUEST} new quips. "
                    "One per line, no numbering, no other text."
                ),
            }
        ],
    )
    text = "".join(block.text for block in reply.content if block.type == "text")
    return parse_quips(text)


class AiQuipSource:
    """Serves AI quips when possible, otherwise quips from the fallback source."""

    def __init__(
        self,
        fallback: QuipSource,
        model: str,
        enabled: bool = True,
        personality: str = "",
        fetch: Callable[[], list[str]] | None = None,
        in_background: bool = True,
        availability: Callable[[], tuple[bool, str]] = ai_available,
    ):
        self._fallback = fallback
        self._fetch = fetch or (lambda: ask_claude(model, self.personality))
        self._in_background = in_background
        self._availability = availability
        self._stock: queue.Queue[str] = queue.Queue()
        self._fetching = threading.Event()
        self._paused_until = 0.0
        self._blocked = False  # e.g. invalid key: stop retrying
        self.enabled = enabled
        self.personality = normalize_personality(personality)

    @property
    def active(self) -> bool:
        return self.enabled and not self._blocked and self._availability()[0]

    def next_quip(self) -> str:
        if self.active:
            try:
                quip = self._stock.get_nowait()
            except queue.Empty:
                quip = None
            self._refill()
            if quip:
                return quip
        return self._fallback.next_quip()

    def set_personality(self, personality: str) -> None:
        """Switch personality and drop old quips so new ones match."""
        self.personality = normalize_personality(personality)
        while True:
            try:
                self._stock.get_nowait()
            except queue.Empty:
                break
        self._paused_until = 0.0
        self.prefetch()

    def prefetch(self) -> None:
        """Fetch quips ahead of time, before the first one is needed."""
        if self.active:
            self._refill()

    def _refill(self) -> None:
        if self._stock.qsize() >= LOW_STOCK or self._fetching.is_set():
            return
        if time.monotonic() < self._paused_until:
            return
        self._fetching.set()
        if self._in_background:
            threading.Thread(target=self._fetch_into_stock, name="ai-quips", daemon=True).start()
        else:
            self._fetch_into_stock()

    def _fetch_into_stock(self) -> None:
        try:
            for quip in self._fetch():
                self._stock.put(quip)
        except Exception as error:  # noqa: BLE001 - the frog must never crash
            self._handle_error(error)
        finally:
            self._fetching.clear()

    def _handle_error(self, error: Exception) -> None:
        try:
            import anthropic
        except ImportError:
            anthropic = None

        if anthropic and isinstance(
            error, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)
        ):
            log.warning("Claude rejected the API key. AI quips stay off. (%s)", error)
            self._blocked = True
        elif anthropic and isinstance(error, anthropic.APIConnectionError):
            log.info("No internet connection? Using the built-in quips for now.")
            self._paused_until = time.monotonic() + PAUSE_AFTER_ERROR_S
        else:
            log.warning("AI quips are unavailable right now: %s", error)
            self._paused_until = time.monotonic() + PAUSE_AFTER_ERROR_S
