import pytest

from frog.model import GROUND_SHARE, Frog, State


def make_frog(**kwargs):
    values = {"x": 100, "speed": 50, "jumps_per_second": 1.0}
    values.update(kwargs)
    return Frog(**values)


def test_one_full_jump_covers_the_average_distance():
    frog = make_frog()
    for _ in range(100):
        frog.step(0.01, 0, 1000)
    assert frog.x == pytest.approx(150)


def test_does_not_move_on_the_ground():
    frog = make_frog()
    frog.step(GROUND_SHARE * 0.9, 0, 1000)
    assert frog.x == 100
    assert not frog.airborne
    assert frog.height == 0


def test_highest_point_is_mid_jump():
    frog = make_frog(jump_height=40)
    frog.phase = GROUND_SHARE + (1 - GROUND_SHARE) / 2
    assert frog.airborne
    assert frog.height == pytest.approx(40)


def test_height_is_never_negative():
    frog = make_frog()
    for _ in range(300):
        frog.step(0.013, 0, 1000)
        assert 0 <= frog.height <= frog.jump_height
        assert 0 <= frog.phase < 1


def test_turns_around_at_the_right_edge():
    frog = make_frog(x=995)
    for _ in range(100):
        frog.step(0.01, 0, 1000)
    assert frog.x <= 1000
    assert frog.direction == -1


def test_turns_around_at_the_left_edge():
    frog = make_frog(x=5, direction=-1)
    for _ in range(100):
        frog.step(0.01, 0, 1000)
    assert frog.x >= 0
    assert frog.direction == 1


def test_sit_lands_immediately_and_stays():
    frog = make_frog()
    frog.phase = 0.6
    frog.sit()
    assert frog.state is State.SITTING
    assert frog.height == 0

    frog.step(1.0, 0, 1000)
    assert frog.x == 100

    frog.start_walking()
    frog.step(0.5, 0, 1000)
    assert frog.x > 100


def test_landing_is_reported():
    frog = make_frog()
    landed = [frog.step(0.1, 0, 1000) for _ in range(25)]
    assert sum(landed) == 2


def test_rests_and_continues_by_itself():
    frog = make_frog()
    frog.rest(2.0)
    frog.step(1.0, 0, 1000)
    assert frog.state is State.RESTING
    assert frog.x == 100
    frog.step(1.5, 0, 1000)
    assert frog.state is State.WALKING


def test_sitting_waits_for_start_walking():
    frog = make_frog()
    frog.sit()
    for _ in range(100):
        frog.step(1.0, 0, 1000)
    assert frog.state is State.SITTING


def test_leaves_the_screen_and_comes_back_from_the_same_side():
    frog = make_frog(x=900, speed=200)
    frog.leave(5.0)
    for _ in range(200):
        frog.step(0.05, 0, 1000, margin=240)
        if frog.state is State.AWAY:
            break
    assert frog.state is State.AWAY
    assert frog.x > 1000 + 240

    frog.step(5.0, 0, 1000, margin=240)  # The break is over
    assert frog.state is State.RETURNING
    assert frog.direction == -1
    assert frog.x == 1000 + 240

    for _ in range(200):
        frog.step(0.05, 0, 1000, margin=240)
        if frog.state is State.WALKING:
            break
    assert frog.state is State.WALKING
    assert 0 <= frog.x <= 1000


def test_does_not_bounce_off_the_edge_while_leaving():
    frog = make_frog(x=990, speed=200)
    frog.leave(5.0)
    for _ in range(20):
        frog.step(0.05, 0, 1000, margin=240)
    assert frog.x > 1000
    assert frog.direction == 1


def test_picked_up_frog_follows_the_mouse_and_falls_when_dropped():
    frog = Frog(x=100, speed=10)
    frog.pick_up()
    frog.hold_at(500, 300)
    assert (frog.state, frog.x, frog.lift) == (State.HELD, 500, 300)
    assert frog.legs_out

    frog.step(1.0, 0, 1000)  # Held frogs do not move by themselves
    assert frog.x == 500 and frog.lift == 300

    frog.drop()
    steps = 0
    while not frog.step(0.02, 0, 1000):
        steps += 1
        assert steps < 100, "the frog never landed"
    assert frog.lift == 0
    assert frog.state is State.RESTING  # Dazed for a moment, then hops on


def test_held_frog_can_not_go_below_the_ground():
    frog = Frog(x=0, speed=10)
    frog.pick_up()
    frog.hold_at(10, -50)
    assert frog.lift == 0


def test_dropped_frog_lands_on_the_screen():
    frog = Frog(x=0, speed=10)
    frog.pick_up()
    frog.hold_at(5000, 10)
    frog.drop()
    frog.step(0.5, 0, 1000)
    assert frog.x == 1000
