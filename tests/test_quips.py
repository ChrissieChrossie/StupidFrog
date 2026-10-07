import random

import pytest

from frog.quips import QUIPS, QuipPicker


def test_never_the_same_quip_twice_in_a_row():
    picker = QuipPicker(rng=random.Random(1))
    previous = picker.next_quip()
    for _ in range(200):
        current = picker.next_quip()
        assert current != previous
        assert current in QUIPS
        previous = current


def test_a_single_quip_works():
    picker = QuipPicker(("Quak",))
    assert picker.next_quip() == "Quak"
    assert picker.next_quip() == "Quak"


def test_no_quips_raises():
    with pytest.raises(ValueError):
        QuipPicker(())
