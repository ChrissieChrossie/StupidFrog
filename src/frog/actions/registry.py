"""List of all actions. Register new actions here."""

from __future__ import annotations

import random

from frog.actions.base import Action
from frog.actions.chatter import SayQuip, TakeBreak, TurnAround
from frog.actions.pranks import (
    HideIcons,
    MoveIcon,
    OpenWindow,
    PackIntoBox,
    PressWindowButton,
)
from frog.quips import QuipSource


def all_actions(quips: QuipSource | None = None) -> list[Action]:
    return [
        SayQuip(quips),
        TurnAround(),
        TakeBreak(),
        OpenWindow(),
        PressWindowButton(),
        HideIcons(),
        MoveIcon(),
        PackIntoBox(),
    ]


def pick_action(actions: list[Action], rng: random.Random | None = None) -> Action | None:
    """Pick a ready action, weighted by `weight`. None if no action is ready."""
    ready = [action for action in actions if action.is_ready()]
    if not ready:
        return None
    rng = rng or random.Random()
    return rng.choices(ready, weights=[action.weight for action in ready], k=1)[0]
