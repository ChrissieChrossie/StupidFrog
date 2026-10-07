import pytest

from frog.screens import Monitor, Screens

LEFT = Monitor(area=(-1920, 0, 0, 1080), work=(-1920, 0, 0, 1040))
MAIN = Monitor(area=(0, 0, 2560, 1440), work=(0, 0, 2560, 1392))


def test_walks_across_all_monitors():
    screens = Screens([MAIN, LEFT])
    assert screens.left == -1920
    assert screens.right == 2560
    assert screens.bounds == (-1920, 0, 2560, 1440)


def test_ground_follows_the_monitor_under_the_frog():
    screens = Screens([MAIN, LEFT])
    assert screens.ground_at(-500) == 1040
    assert screens.ground_at(500) == 1392


def test_stacked_monitors_use_the_lower_one():
    top = Monitor(area=(0, -1080, 1920, 0), work=(0, -1080, 1920, 0))
    screens = Screens([top, MAIN])
    assert screens.ground_at(100) == 1392


def test_gap_between_monitors_uses_the_nearest():
    right = Monitor(area=(3000, 0, 4920, 1080), work=(3000, 0, 4920, 1040))
    screens = Screens([MAIN, right])
    assert screens.ground_at(2600) == 1392
    assert screens.ground_at(2950) == 1040


def test_without_monitor_info_one_screen_is_assumed():
    class NoMonitors:
        @staticmethod
        def monitors():
            return []

    screens = Screens.detect(1920, 1080, 48, system=NoMonitors)
    assert (screens.left, screens.right) == (0, 1920)
    assert screens.ground_at(10) == 1032


def test_needs_a_monitor():
    with pytest.raises(ValueError):
        Screens([])
