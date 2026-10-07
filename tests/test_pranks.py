import random

from frog.actions.pranks import HideIcons, MoveIcon, OpenWindow, PackIntoBox, PressWindowButton

# --- Open window --------------------------------------------------------------


class FakeMinimized:
    def __init__(self, windows):
        self.windows = windows
        self.restored = []

    def is_available(self):
        return True

    def minimized_windows(self):
        return self.windows

    def restore_window(self, hwnd):
        self.restored.append(hwnd)


def test_restores_a_minimized_window(context):
    system = FakeMinimized([(42, "Rechner")])
    OpenWindow(system).run(context)
    assert system.restored == [42]
    assert "Rechner" in context.said[0]


def test_without_minimized_windows_nothing_happens(context):
    system = FakeMinimized([])
    OpenWindow(system).run(context)
    assert system.restored == []
    assert context.said


# --- Window buttons -----------------------------------------------------------


class FakeButtons:
    def __init__(self, windows, maximized=False):
        self.windows = windows
        self.maximized = maximized
        self.pressed = []
        self.gone = False

    def is_available(self):
        return True

    def open_windows(self):
        return self.windows

    def button_position(self, hwnd, button):
        return {"minimize": (900, 10), "maximize": (950, 10)}[button]

    def window_exists(self, hwnd):
        return not self.gone

    def is_maximized(self, hwnd):
        return self.maximized

    def minimize_window(self, hwnd):
        self.pressed.append("minimized")

    def maximize_window(self, hwnd):
        self.pressed.append("maximized")

    def restore_window(self, hwnd):
        self.pressed.append("restored")


def always_pick(button):
    """An RNG that always picks the given button."""

    class Rng(random.Random):
        def choice(self, seq):
            return button if button in seq else seq[0]

    return Rng()


def test_tongue_presses_minimize(context):
    system = FakeButtons([(7, "Editor")])
    PressWindowButton(system, always_pick("minimize")).run(context)
    assert context.licked == [(900, 10)]
    assert system.pressed == ["minimized"]
    assert len(context.said) == 2  # Before and after


def test_tongue_presses_maximize(context):
    system = FakeButtons([(7, "Editor")])
    PressWindowButton(system, always_pick("maximize")).run(context)
    assert context.licked == [(950, 10)]
    assert system.pressed == ["maximized"]


def test_maximized_window_is_restored(context):
    system = FakeButtons([(7, "Editor")], maximized=True)
    PressWindowButton(system, always_pick("maximize")).run(context)
    assert system.pressed == ["restored"]


def test_closed_window_is_not_pressed(context):
    system = FakeButtons([(7, "Editor")])
    system.gone = True
    PressWindowButton(system, always_pick("minimize")).run(context)
    assert system.pressed == []
    assert context.said


def test_no_open_windows_no_tongue(context):
    system = FakeButtons([])
    PressWindowButton(system).run(context)
    assert context.licked == []
    assert context.said


# --- Hide icons ---------------------------------------------------------------


class FakeIcons:
    def __init__(self, positions=((10, 10), (10, 100)), auto_arranged=False):
        self.shown = True
        self.places = list(positions)
        self.arranged = auto_arranged

    def auto_arranged(self):
        return self.arranged

    def size(self):
        return 1920, 1080

    def positions(self):
        return list(self.places)

    def move(self, index, position):
        self.places[index] = position

    def screen_point(self, position):
        return position

    def visible(self):
        return self.shown

    def hide(self):
        self.shown = False

    def show(self):
        self.shown = True


class FakeDesktop:
    def __init__(self, icons=None):
        self.icons = icons or FakeIcons()
        self.windows = [(1, "Editor"), (2, "Mail")]  # Top to bottom
        self.minimized = []
        self.restored = []
        desktop = self

        class DesktopIcons:
            @staticmethod
            def find():
                return desktop.icons

        self.DesktopIcons = DesktopIcons

    def is_available(self):
        return True

    def open_windows(self):
        return list(self.windows)

    def minimize_window(self, hwnd):
        self.minimized.append(hwnd)

    def window_exists(self, hwnd):
        return any(h == hwnd for h, _ in self.windows)

    def restore_window(self, hwnd):
        self.restored.append(hwnd)


def test_icons_are_hidden_and_come_back(context):
    system = FakeDesktop()
    HideIcons(system).run(context)
    assert not system.icons.shown

    context.scheduled[0]()  # Time passes ...
    assert system.icons.shown
    assert len(context.said) == 2  # When hiding and when bringing them back


def test_icons_are_back_after_cleanup(context):
    system = FakeDesktop()
    action = HideIcons(system)
    action.run(context)
    action.cleanup()
    assert system.icons.shown


def test_hiding_twice_schedules_only_once(context):
    system = FakeDesktop()
    action = HideIcons(system)
    action.run(context)
    action.run(context)
    assert len(context.scheduled) == 1


def test_not_ready_without_windows():
    class NotWindows:
        def is_available(self):
            return False

    for prank in (HideIcons, MoveIcon, OpenWindow, PressWindowButton):
        assert not prank(NotWindows()).is_ready()


def test_every_prank_says_something(context):
    PackIntoBox().run(context)
    OpenWindow(FakeMinimized([(1, "Mail")])).run(context)
    HideIcons(FakeDesktop()).run(context)
    assert len(context.said) == 3


# --- Move icons ---------------------------------------------------------------


def test_shows_desktop_flicks_icon_and_reopens_windows(context):
    system = FakeDesktop()
    before = system.icons.positions()
    MoveIcon(system).run(context)
    assert system.minimized == [1, 2]

    context.scheduled.pop(0)()  # Desktop is visible, out comes the tongue
    assert context.licked and context.licked[0] in before
    assert system.icons.positions() != before

    context.scheduled.pop(0)()  # Time passes ...
    assert system.restored == [2, 1]  # Bottom window first, so the top one stays on top
    assert system.icons.positions() != before  # The icon stays where it landed
    assert len(context.said) == 2


def test_closed_window_is_not_reopened(context):
    system = FakeDesktop()
    MoveIcon(system).run(context)
    system.windows = [(2, "Mail")]  # The user closed the editor meanwhile
    context.scheduled.pop(0)()
    context.scheduled.pop(0)()
    assert system.restored == [2]


def test_windows_come_back_after_cleanup(context):
    system = FakeDesktop()
    action = MoveIcon(system)
    action.run(context)
    action.cleanup()
    assert system.restored == [2, 1]


def test_auto_arrange_spoils_the_fun(context):
    system = FakeDesktop(FakeIcons(auto_arranged=True))
    MoveIcon(system).run(context)
    assert not context.licked and not system.minimized
    assert context.said[0] in MoveIcon.AUTO_ARRANGED


def test_moves_only_one_icon_at_a_time(context):
    system = FakeDesktop()
    action = MoveIcon(system)
    action.run(context)
    action.run(context)
    assert len(context.scheduled) == 1


# --- Pack into box ------------------------------------------------------------


def test_empty_playground_gets_bait_files(context):
    PackIntoBox().run(context)
    playground = context.settings.playground
    assert sorted(p.name for p in playground.glob("*.txt")) == sorted(PackIntoBox.BAIT_FILES)


def test_packs_one_file_into_the_box(context):
    action = PackIntoBox(random.Random(0))
    action.run(context)  # Lay bait
    action.run(context)  # Pack one file
    playground = context.settings.playground
    assert len(list((playground / PackIntoBox.BOX).iterdir())) == 1
    assert len(list(playground.glob("*.txt"))) == len(PackIntoBox.BAIT_FILES) - 1


def test_full_box_is_emptied(context):
    action = PackIntoBox(random.Random(0))
    for _ in range(1 + len(PackIntoBox.BAIT_FILES)):
        action.run(context)
    playground = context.settings.playground
    assert not list(playground.glob("*.txt"))

    action.run(context)
    assert len(list(playground.glob("*.txt"))) == len(PackIntoBox.BAIT_FILES)
    assert not list((playground / PackIntoBox.BOX).iterdir())


def test_files_outside_stay_untouched(context, tmp_path):
    real_file = tmp_path / "important.txt"
    real_file.write_text("hands off", encoding="utf-8")
    action = PackIntoBox(random.Random(0))
    for _ in range(20):
        action.run(context)
    assert real_file.read_text(encoding="utf-8") == "hands off"


def test_link_to_outside_is_ignored(context, tmp_path):
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")
    playground = context.settings.playground
    playground.mkdir(parents=True)
    (playground / "link.txt").symlink_to(outside)

    action = PackIntoBox(random.Random(0))
    for _ in range(10):
        action.run(context)
    assert (playground / "link.txt").is_symlink()
    assert outside.read_text(encoding="utf-8") == "secret"


def test_never_overwrites_anything(context):
    playground = context.settings.playground
    (playground / PackIntoBox.BOX).mkdir(parents=True)
    (playground / PackIntoBox.BOX / "letter.txt").write_text("old", encoding="utf-8")
    (playground / "letter.txt").write_text("new", encoding="utf-8")

    PackIntoBox(random.Random(0)).run(context)
    assert (playground / PackIntoBox.BOX / "letter.txt").read_text(encoding="utf-8") == "old"
    assert (playground / "letter.txt").read_text(encoding="utf-8") == "new"
