"""German jokes from JokeAPI (https://v2.jokeapi.dev), mixed in while the AI quips are off.

How it works:
- The frog keeps a small stock of jokes, fetched in the background.
- Only "safe" jokes are requested (no offensive, political or religious jokes).
- Jokes that would not fit into the speech bubble are skipped.
- Without internet the built-in list is used, as always.
"""

from __future__ import annotations

import json
import logging
import random
import threading
import time
import urllib.request
from collections.abc import Callable

from frog.quips import QuipSource

log = logging.getLogger(__name__)

API_URL = "https://v2.jokeapi.dev/joke/Any?lang=de&safe-mode&amount=10"
TIMEOUT_S = 10.0
MAX_JOKE_CHARS = 120  # Longer jokes do not fit into the speech bubble
JOKE_SHARE = 0.4  # How often a joke is told instead of a built-in quip
LOW_STOCK = 3
PAUSE_AFTER_ERROR_S = 300.0


def parse_jokes(data: dict) -> list[str]:
    """Turn a JokeAPI reply into a list of jokes that fit into the speech bubble."""
    if data.get("error"):
        return []
    entries = data["jokes"] if "jokes" in data else [data]
    jokes = []
    for entry in entries:
        if entry.get("type") == "twopart":
            text = f"{entry.get('setup', '').strip()}\n{entry.get('delivery', '').strip()}"
        else:
            text = entry.get("joke", "").strip()
        if text.strip() and len(text) <= MAX_JOKE_CHARS:
            jokes.append(text)
    return jokes


def fetch_jokes() -> list[str]:
    request = urllib.request.Request(API_URL, headers={"User-Agent": "StupidFrog"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as reply:
        return parse_jokes(json.load(reply))


class JokeSource:
    """Tells a joke now and then, otherwise a quip from the fallback source."""

    def __init__(
        self,
        fallback: QuipSource,
        enabled: bool = True,
        rng: random.Random | None = None,
        fetch: Callable[[], list[str]] = fetch_jokes,
        in_background: bool = True,
    ):
        self._fallback = fallback
        self._rng = rng or random.Random()
        self._fetch = fetch
        self._in_background = in_background
        self._stock: list[str] = []
        self._told: set[str] = set()  # The German pool is small: avoid repeats
        self._lock = threading.Lock()
        self._fetching = threading.Event()
        self._paused_until = 0.0
        self.enabled = enabled

    def next_quip(self) -> str:
        if not self.enabled:
            return self._fallback.next_quip()
        self._refill()
        with self._lock:
            joke = self._stock.pop(0) if self._stock and self._rng.random() < JOKE_SHARE else None
        if joke:
            self._told.add(joke)
            return joke
        return self._fallback.next_quip()

    def prefetch(self) -> None:
        if self.enabled:
            self._refill()

    def _refill(self) -> None:
        if len(self._stock) >= LOW_STOCK or self._fetching.is_set():
            return
        if time.monotonic() < self._paused_until:
            return
        self._fetching.set()
        if self._in_background:
            threading.Thread(target=self._fetch_into_stock, name="jokes", daemon=True).start()
        else:
            self._fetch_into_stock()

    def _fetch_into_stock(self) -> None:
        try:
            jokes = dict.fromkeys(self._fetch())
            new = [j for j in jokes if j not in self._told and j not in self._stock]
            if not new:
                # Heard them all: take a break, then old jokes are allowed again
                self._told.clear()
                self._paused_until = time.monotonic() + PAUSE_AFTER_ERROR_S
            with self._lock:
                self._stock.extend(new)
        except Exception as error:  # noqa: BLE001 - the frog must never crash
            log.info("No jokes from JokeAPI right now: %s", error)
            self._paused_until = time.monotonic() + PAUSE_AFTER_ERROR_S
        finally:
            self._fetching.clear()
