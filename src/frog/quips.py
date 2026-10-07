"""The built-in quips (German, since the frog speaks German). Add new ones to the list."""

from __future__ import annotations

import random
from typing import Protocol

QUIPS: tuple[str, ...] = (
    "Ich bin hier der Desktop-Manager. Nur damit das klar ist.",
    "So viele offene Fenster. Ganz toll organisiert.",
    "Dein Download-Ordner hat mehr Chaos als ein Sumpf.",
    "Oh, du arbeitest? Hätte ich jetzt nicht gedacht.",
    "Ich räume hier auf. Du machst ja nichts.",
    "Schon wieder dieses Fenster? Mutig.",
    "Speichern? Ach was, wird schon gutgehen.",
    "Ohne mich wäre dieser Desktop längst untergegangen.",
    "Beeindruckend, wie lange man auf ein Fenster starren kann.",
    "Ich hätte gern eine Gehaltserhöhung. In Fliegen.",
    "Papierkorb voll, Kopf leer. Läuft bei dir.",
    "Noch ein Tab? Klar, warum nicht.",
)


class QuipSource(Protocol):
    def next_quip(self) -> str: ...


class QuipPicker:
    """Returns random quips, never the same one twice in a row."""

    def __init__(self, quips: tuple[str, ...] = QUIPS, rng: random.Random | None = None):
        if not quips:
            raise ValueError("Without quips the frog would be mute.")
        self._quips = quips
        self._rng = rng or random.Random()
        self._last: str | None = None

    def next_quip(self) -> str:
        choices = [q for q in self._quips if q != self._last] or list(self._quips)
        self._last = self._rng.choice(choices)
        return self._last
