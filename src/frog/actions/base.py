"""Building blocks shared by all actions."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Protocol

from frog.config import Settings
from frog.model import Frog

Task = Callable[[], None]


class Context(Protocol):
    """What an action is allowed to use. The app provides it, tests use a fake."""

    frog: Frog
    settings: Settings

    def say(self, text: str) -> None: ...

    def later(self, milliseconds: int, task: Task) -> object: ...

    def tongue(self, x: int, y: int, on_hit: Task) -> None:
        """Stick the tongue out to screen point (x, y) and call `on_hit` when it arrives."""
        ...


class Action(ABC):
    """Something the frog can do.

    To add an action:
    1. Subclass `Action`.
    2. Set `name` and implement `run`.
    3. Register it in `registry.py`.
    """

    name: str = "unnamed"  # Shown in the context menu, therefore German
    weight: int = 1  # Higher weight means the action is picked more often
    setting_key: str | None = None  # Key of the menu switch; None means no switch
    enabled: bool = True

    def can_run(self) -> bool:
        """False if the action is impossible on this computer (e.g. not Windows)."""
        return True

    def is_ready(self) -> bool:
        return self.enabled and self.can_run()

    def cleanup(self) -> None:
        """Called on exit and when switched off. Undo pranks here."""
        return None

    @abstractmethod
    def run(self, context: Context) -> None: ...


class QuippingAction(Action):
    """An action that comments on what it does with a random line."""

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()

    def _say_one_of(self, context: Context, lines: tuple[str, ...], **values: str) -> None:
        context.say(self._rng.choice(lines).format(**values))
