import random

from frog.reactions import REMINDERS, MouseChase, Reaction, Reminders


class FixedRandom(random.Random):
    def __init__(self, value):
        super().__init__(0)
        self.value = value

    def random(self):
        return self.value


def test_close_mouse_makes_the_frog_snap():
    chase = MouseChase(radius=100, cooldown_s=10, rng=FixedRandom(0.1))
    assert chase.react(0, (0, 0), (50, 50), on_frog=False) is Reaction.SNAP


def test_close_mouse_can_make_the_frog_flee():
    chase = MouseChase(radius=100, cooldown_s=10, rng=FixedRandom(0.9))
    assert chase.react(0, (0, 0), (50, 50), on_frog=False) is Reaction.FLEE


def test_far_mouse_is_ignored():
    chase = MouseChase(radius=100, cooldown_s=10)
    assert chase.react(0, (0, 0), (90, 90), on_frog=False) is None


def test_mouse_on_the_frog_is_ignored_so_it_can_be_grabbed():
    chase = MouseChase(radius=100, cooldown_s=10)
    assert chase.react(0, (0, 0), (5, 5), on_frog=True) is None


def test_cooldown_between_reactions():
    chase = MouseChase(radius=100, cooldown_s=10)
    assert chase.react(0, (0, 0), (5, 5), on_frog=False)
    assert chase.react(5, (0, 0), (5, 5), on_frog=False) is None
    assert chase.react(11, (0, 0), (5, 5), on_frog=False)


def test_switched_off_chase_does_nothing():
    chase = MouseChase(radius=100, cooldown_s=10, enabled=False)
    assert chase.react(0, (0, 0), (5, 5), on_frog=False) is None


def test_reminder_comes_after_the_interval():
    reminders = Reminders(interval_s=60, now=0)
    assert reminders.due(30) is None
    assert reminders.due(60) in REMINDERS
    assert reminders.due(90) is None
    assert reminders.due(120) in REMINDERS


def test_switched_off_reminders_stay_quiet():
    reminders = Reminders(interval_s=60, now=0, enabled=False)
    assert reminders.due(1000) is None


def test_restart_counts_from_now():
    reminders = Reminders(interval_s=60, now=0)
    reminders.restart(100)
    assert reminders.due(150) is None
    assert reminders.due(160) in REMINDERS
