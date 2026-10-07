"""How the frog reacts to the user: the mouse, being picked up, and reminders.

The (German) lines are shown to the user.
"""

from __future__ import annotations

import random
from enum import Enum, auto

Point = tuple[float, float]

PICKED_UP = (
    "Hey! Lass mich runter!",
    "Huch! Ich bin doch kein Spielzeug!",
    "Uiii, ich kann fliegen!",
    "Finger weg vom Desktop-Manager!",
)
DROPPED = (
    "Aua! Mach das nie wieder.",
    "Gelandet. Note: sechs.",
    "Nochmal! Nein, war nur Spaß.",
    "Das melde ich dem Betriebsrat.",
)
SNAPPED = (
    "Schnapp! Lecker Mauszeiger.",
    "Hab dich fast, du Pfeil!",
    "Der Mauszeiger schmeckt nach Plastik.",
    "Zunge schneller als deine Hand!",
)
FLED = (
    "Finger weg! Ich bin beschäftigt.",
    "Bleib mir mit der Maus vom Leib!",
    "Ich hab dich gesehen. Tschüss!",
)
REMINDERS = (
    "Trink mal was! Wasser, nicht Kaffee.",
    "Steh mal auf und streck dich. Ich pass so lange auf.",
    "Augen weg vom Bildschirm! 20 Sekunden aus dem Fenster gucken.",
    "Pause! Selbst ich hüpfe nicht den ganzen Tag.",
    "Schultern runter. Du sitzt wie ein Fragezeichen.",
    "Hast du heute schon was gegessen? Fliegen zählen nicht.",
)


class Reaction(Enum):
    SNAP = auto()  # Stick the tongue out at the mouse
    FLEE = auto()  # Hop away from the mouse


class MouseChase:
    """Decides whether the frog reacts to a mouse pointer that comes close."""

    SNAP_SHARE = 0.6  # The rest of the time the frog hops away

    def __init__(
        self,
        radius: float,
        cooldown_s: float,
        enabled: bool = True,
        rng: random.Random | None = None,
    ):
        self.radius = radius
        self.cooldown_s = cooldown_s
        self.enabled = enabled
        self._rng = rng or random.Random()
        self._next_allowed = 0.0

    def react(self, now: float, frog: Point, pointer: Point, on_frog: bool) -> Reaction | None:
        """`on_frog` is True while the pointer is over the frog (the user may want to grab it)."""
        if not self.enabled or on_frog or now < self._next_allowed:
            return None
        dx, dy = pointer[0] - frog[0], pointer[1] - frog[1]
        if dx * dx + dy * dy > self.radius * self.radius:
            return None
        self._next_allowed = now + self.cooldown_s
        return Reaction.SNAP if self._rng.random() < self.SNAP_SHARE else Reaction.FLEE


class Reminders:
    """Hands out a reminder line every `interval_s` seconds."""

    def __init__(
        self,
        interval_s: float,
        now: float,
        enabled: bool = True,
        rng: random.Random | None = None,
    ):
        self.interval_s = interval_s
        self.enabled = enabled
        self._rng = rng or random.Random()
        self._next_due = now + interval_s

    def due(self, now: float) -> str | None:
        if not self.enabled or now < self._next_due:
            return None
        self._next_due = now + self.interval_s
        return self._rng.choice(REMINDERS)

    def restart(self, now: float) -> None:
        """Start counting again, e.g. after the reminders were switched back on."""
        self._next_due = now + self.interval_s
