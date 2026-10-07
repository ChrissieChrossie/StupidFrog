"""Simple actions: talking, turning around and taking a break."""

from __future__ import annotations

from frog.actions.base import Action, Context, QuippingAction
from frog.model import State
from frog.quips import QuipPicker, QuipSource


class SayQuip(Action):
    name = "Spruch sagen"
    WEIGHT_DEFAULT = 5
    WEIGHT_WITH_AI = 12  # With AI quips the frog talks a lot more

    def __init__(self, quips: QuipSource | None = None):
        self._quips = quips or QuipPicker()

    @property
    def weight(self) -> int:
        ai_active = getattr(self._quips, "active", False)
        return self.WEIGHT_WITH_AI if ai_active else self.WEIGHT_DEFAULT

    def run(self, context: Context) -> None:
        context.say(self._quips.next_quip())


class TurnAround(Action):
    name = "Umdrehen"
    weight = 2

    def run(self, context: Context) -> None:
        context.frog.turn_around()
        context.say("Ach nee, doch da lang.")


class TakeBreak(QuippingAction):
    """Now and then the frog has had enough, hops off the screen and comes back later."""

    name = "Ab und zu Pause machen"
    setting_key = "take_break"
    CHECK_RETURN_MS = 500

    LEAVING = (
        "Keine Lust mehr. Ich bin dann mal weg.",
        "Mittagspause. Der Desktop muss jetzt ohne mich klarkommen.",
        "Ich geh mal Fliegen fangen.",
        "Feierabend! Zumindest kurz.",
    )
    RETURNED = (
        "Bin wieder da. Hast du mich vermisst?",
        "So, Pause vorbei. Wer hat hier Chaos gemacht?",
        "Der Desktop-Manager ist zurück!",
        "Ich war nur kurz weg und schon alles durcheinander.",
    )

    def run(self, context: Context) -> None:
        s = context.settings
        self._say_one_of(context, self.LEAVING)
        context.frog.leave(self._rng.uniform(s.break_min_s, s.break_max_s))
        context.later(self.CHECK_RETURN_MS, lambda: self._greet_when_back(context))

    def _greet_when_back(self, context: Context) -> None:
        if context.frog.state is State.WALKING:
            self._say_one_of(context, self.RETURNED)
        else:
            context.later(self.CHECK_RETURN_MS, lambda: self._greet_when_back(context))
