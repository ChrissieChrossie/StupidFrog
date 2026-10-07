import random

from frog.actions import Action, all_actions, pick_action
from frog.actions.chatter import SayQuip, TurnAround
from frog.quips import QuipPicker


def test_say_quip(context):
    SayQuip(QuipPicker(("Quak",))).run(context)
    assert context.said == ["Quak"]


def test_turn_around(context):
    TurnAround().run(context)
    assert context.frog.direction == -1
    assert context.said


def test_picked_actions_are_always_ready():
    rng = random.Random(0)
    actions = all_actions()
    for _ in range(500):
        picked = pick_action(actions, rng)
        assert picked is not None
        assert picked.is_ready()


def test_no_ready_action_returns_none():
    class Off(Action):
        def is_ready(self):
            return False

        def run(self, context):
            raise AssertionError("must not run")

    assert pick_action([Off()]) is None


def test_all_actions_have_a_name_and_weight():
    for action in all_actions():
        assert action.name != "unnamed"
        assert action.weight > 0


def test_disabled_action_is_never_picked():
    actions = all_actions()
    for action in actions:
        if action.setting_key:
            action.enabled = False
    rng = random.Random(0)
    for _ in range(200):
        assert pick_action(actions, rng).setting_key is None


def test_talks_more_with_ai():
    class Ai:
        active = True

        def next_quip(self):
            return "Quak"

    with_ai = SayQuip(Ai())
    without_ai = SayQuip(QuipPicker(("Quak",)))
    assert with_ai.weight > without_ai.weight
    Ai.active = False
    assert with_ai.weight == without_ai.weight


def test_take_break_leaves_and_greets_on_return(context):
    from frog.actions.chatter import TakeBreak
    from frog.model import State

    TakeBreak(random.Random(0)).run(context)
    assert context.frog.state is State.LEAVING
    assert len(context.said) == 1

    context.scheduled.pop(0)()  # Still away: checks again later
    assert len(context.said) == 1

    context.frog.start_walking()  # Back on screen
    context.scheduled.pop(0)()
    assert len(context.said) == 2
