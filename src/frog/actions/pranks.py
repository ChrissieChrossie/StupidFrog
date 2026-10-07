"""Real desktop pranks. Each one has its own switch in the context menu.

All of them are harmless and reversible:
- Open window: the user can simply minimize it again.
- Window buttons: the tongue presses minimize or maximize.
- Hide icons: they come back after a few seconds.
- Move icons: windows are minimized and reopened afterwards; the icon stays
  where it lands, the user can simply drag it back.
- Pack into box: only inside the playground, files are never deleted.

The frog comments on every prank. The (German) lines are listed in each class.
"""

from __future__ import annotations

import logging
import random
from pathlib import Path

from frog import windows
from frog.actions.base import Context, QuippingAction
from frog.safety import OutsidePlayground, safe_path

log = logging.getLogger(__name__)


def _shorten(text: str, length: int = 30) -> str:
    return text if len(text) <= length else text[: length - 1] + "…"


class OpenWindow(QuippingAction):
    """Restores a minimized window."""

    name = "Minimierte Fenster öffnen"
    setting_key = "open_window"

    OPENED = (
        'Kuckuck! "{title}" hatte sich versteckt.',
        'Ich hab "{title}" gefunden! Wer suchen will, muss quaken.',
        'Hoppla, "{title}" ist wieder da. Ganz aus Versehen. Hihi.',
        'Was macht "{title}" denn da unten? Raus da!',
    )
    NOTHING = (
        "Nix versteckt hier. Langweilig.",
        "Alle Fenster schon offen? Spielverderber.",
    )

    def __init__(self, system=windows, rng: random.Random | None = None):
        super().__init__(rng)
        self._system = system

    def can_run(self) -> bool:
        return self._system.is_available()

    def run(self, context: Context) -> None:
        candidates = self._system.minimized_windows()
        if not candidates:
            self._say_one_of(context, self.NOTHING)
            return
        hwnd, title = self._rng.choice(candidates)
        self._system.restore_window(hwnd)
        self._say_one_of(context, self.OPENED, title=_shorten(title))


class PressWindowButton(QuippingAction):
    """Uses the tongue to press minimize or maximize on an open window."""

    name = "Fenster-Knöpfe mit der Zunge drücken"
    setting_key = "window_buttons"

    BEFORE = (
        "Schlabber-Attacke!",
        "Achtung, Zunge kommt!",
        "Mal sehen, was dieser Knopf macht ...",
        "Ich hab Hunger auf Knöpfe!",
    )
    MINIMIZED = (
        'Schlurp! "{title}" ist weg.',
        '"{title}" hab ich verschluckt. Lecker!',
        'Ups, "{title}" ist in die Taskleiste gefallen.',
    )
    MAXIMIZED = (
        'Bämm! "{title}" ist jetzt riesig.',
        'Ich hab "{title}" aufgeblasen. Wie ein Frosch!',
        '"{title}" ganz groß. Jetzt siehst du besser, oder?',
    )
    RESTORED = (
        '"{title}" war mir zu groß. Jetzt passt es.',
        'Schrumpf! "{title}" ist wieder klein.',
    )
    MISSED = ("Daneben! Das Fenster ist abgehauen.",)
    NOTHING = (
        "Kein Fenster zum Ablecken da. Schade.",
        "Wo sind denn alle Fenster hin?",
    )

    def __init__(self, system=windows, rng: random.Random | None = None):
        super().__init__(rng)
        self._system = system

    def can_run(self) -> bool:
        return self._system.is_available()

    def run(self, context: Context) -> None:
        candidates = self._system.open_windows()
        if not candidates:
            self._say_one_of(context, self.NOTHING)
            return
        hwnd, title = self._rng.choice(candidates)
        button = self._rng.choice(("minimize", "maximize"))
        target = self._system.button_position(hwnd, button)
        if target is None:
            return
        self._say_one_of(context, self.BEFORE)
        context.tongue(*target, lambda: self._press(context, hwnd, _shorten(title), button))

    def _press(self, context: Context, hwnd: int, title: str, button: str) -> None:
        """Called when the tongue reaches the button."""
        if not self._system.window_exists(hwnd):
            self._say_one_of(context, self.MISSED)
        elif button == "minimize":
            self._system.minimize_window(hwnd)
            self._say_one_of(context, self.MINIMIZED, title=title)
        elif self._system.is_maximized(hwnd):
            # On a maximized window this button restores the normal size.
            self._system.restore_window(hwnd)
            self._say_one_of(context, self.RESTORED, title=title)
        else:
            self._system.maximize_window(hwnd)
            self._say_one_of(context, self.MAXIMIZED, title=title)


class HideIcons(QuippingAction):
    """Briefly hides all desktop icons, then shows them again."""

    name = "Desktop-Symbole verstecken"
    setting_key = "hide_icons"
    RETURN_AFTER_MS = 5000

    HIDDEN = (
        "Hihi, ich hab deine Symbole versteckt!",
        "Simsalabim! Alle Symbole weg.",
        "Wo sind deine Symbole? Ich sag nix.",
        "Ich hab deine Symbole gefressen. Bäh, schmeckt nach Pixel.",
    )
    RETURNED = (
        "Na gut, hier sind sie wieder.",
        "Okay, ich spuck sie wieder aus.",
        "War nur Spaß! Alles wieder da.",
    )
    NOTHING = ("Wo sind denn deine Desktop-Symbole hin?",)

    def __init__(self, system=windows, rng: random.Random | None = None):
        super().__init__(rng)
        self._system = system
        self._hidden = None  # The icons that are currently hidden

    def can_run(self) -> bool:
        return self._system.is_available()

    def run(self, context: Context) -> None:
        if self._hidden is not None:
            return
        icons = self._system.DesktopIcons.find()
        if icons is None or not icons.visible():
            self._say_one_of(context, self.NOTHING)
            return
        icons.hide()
        self._hidden = icons
        self._say_one_of(context, self.HIDDEN)

        def bring_back() -> None:
            if self._show_icons():
                self._say_one_of(context, self.RETURNED)

        context.later(self.RETURN_AFTER_MS, bring_back)

    def cleanup(self) -> None:
        self._show_icons()

    def _show_icons(self) -> bool:
        if self._hidden is None:
            return False
        self._hidden.show()
        self._hidden = None
        return True


class MoveIcon(QuippingAction):
    """Shows the desktop, flicks an icon to another spot with the tongue, then reopens the windows.

    The icon stays where it lands.
    """

    name = "Desktop-Symbole verschieben"
    setting_key = "move_icons"
    SHOW_DESKTOP_MS = 800  # Give the windows time to get out of the way
    REOPEN_AFTER_MS = 1500  # Let the user see the new spot before the windows come back
    EDGE = 80  # Keep moved icons this far away from the edges (pixels)

    BEFORE = (
        "Platz da, ich muss an den Desktop!",
        "Moment, ich räum mal kurz um.",
        "Fenster weg! Hier muss umdekoriert werden.",
        "Als Desktop-Manager sage ich: Das gehört woanders hin.",
    )
    MOVED = (
        "Schlurp! Viel besser da drüben.",
        "So. Jetzt ist der Desktop endlich ordentlich.",
        "Ups, abgerutscht. Such es mal!",
        "Feng-Shui für Frösche. Bitte, gern geschehen.",
    )
    AUTO_ARRANGED = (
        "Du hast Automatisch anordnen an. Spielverderber!",
        "Deine Symbole kleben fest. Langweilig.",
    )
    NOTHING = ("Keine Symbole zum Verschieben da. Schade.",)

    def __init__(self, system=windows, rng: random.Random | None = None):
        super().__init__(rng)
        self._system = system
        self._hidden_windows: list | None = None  # Minimized by us, reopened afterwards

    def can_run(self) -> bool:
        return self._system.is_available()

    def run(self, context: Context) -> None:
        if self._hidden_windows is not None:
            return
        icons = self._system.DesktopIcons.find()
        if icons is None or not icons.visible():
            self._say_one_of(context, self.NOTHING)
            return
        if icons.auto_arranged():
            self._say_one_of(context, self.AUTO_ARRANGED)
            return
        positions = icons.positions()
        if not positions:
            self._say_one_of(context, self.NOTHING)
            return

        self._hidden_windows = self._system.open_windows()
        for hwnd, _title in self._hidden_windows:
            self._system.minimize_window(hwnd)
        self._say_one_of(context, self.BEFORE)

        index = self._rng.randrange(len(positions))
        context.later(
            self.SHOW_DESKTOP_MS,
            lambda: context.tongue(
                *icons.screen_point(positions[index]),
                lambda: self._flick(context, icons, index),
            ),
        )

    def cleanup(self) -> None:
        self._reopen_windows()

    def _flick(self, context: Context, icons, index: int) -> None:
        """Called when the tongue reaches the icon."""
        width, height = icons.size()
        if width > 2 * self.EDGE and height > 2 * self.EDGE:
            target = (
                self._rng.randint(self.EDGE, width - self.EDGE),
                self._rng.randint(self.EDGE, height - self.EDGE),
            )
            icons.move(index, target)
            self._say_one_of(context, self.MOVED)
        context.later(self.REOPEN_AFTER_MS, self._reopen_windows)

    def _reopen_windows(self) -> None:
        if self._hidden_windows is None:
            return
        # The list is ordered top to bottom; restore the bottom one first
        # so the previously active window ends up on top again.
        for hwnd, _title in reversed(self._hidden_windows):
            if self._system.window_exists(hwnd):
                self._system.restore_window(hwnd)
        self._hidden_windows = None


class PackIntoBox(QuippingAction):
    """Tidies files in the playground into a box folder. Only there!"""

    name = "Dinge in Ordner packen"
    setting_key = "pack_into_box"
    BOX = "Froschkiste"  # Folder name the user sees, therefore German
    BAIT_FILES = ("fliege.txt", "seerose.txt", "regenwurm.txt", "teich-plan.txt")
    BAIT_TEXT = "Diese Datei hat der Frosch gemacht. Du darfst sie löschen.\n"

    PACKED = (
        "Aufgeräumt! {file} ist jetzt in der Froschkiste.",
        "Zack, {file} ist weggepackt. Ordnung muss sein!",
        "{file}? Hab ich in meine Kiste getan. Meins!",
    )
    EMPTIED = (
        "Kiste ausgekippt! Alles wieder durcheinander.",
        "Huch, die Kiste ist umgefallen. Ganz aus Versehen.",
    )
    BAITED = (
        "Ich hab dir was in die Frosch-Spielwiese gelegt.",
        "Schau mal in die Frosch-Spielwiese. Geschenke!",
    )

    def run(self, context: Context) -> None:
        playground = Path(context.settings.playground)
        playground.mkdir(parents=True, exist_ok=True)
        playground = safe_path(playground, ".")
        box = safe_path(playground, self.BOX)
        box.mkdir(exist_ok=True)

        loose = self._safe_files(playground, playground)
        boxed = self._safe_files(playground, box)

        if loose:
            self._pack_one(context, playground, self._rng.choice(loose))
        elif boxed:
            self._empty_box(context, playground, boxed)
        else:
            self._lay_bait(context, playground)

    def _pack_one(self, context: Context, playground: Path, file: Path) -> None:
        target = safe_path(playground, Path(self.BOX) / file.name)
        if target.exists():
            return  # Never overwrite anything
        file.rename(target)
        self._say_one_of(context, self.PACKED, file=_shorten(file.name))

    def _empty_box(self, context: Context, playground: Path, boxed: list[Path]) -> None:
        for file in boxed:
            target = safe_path(playground, file.name)
            if not target.exists():
                file.rename(target)
        self._say_one_of(context, self.EMPTIED)

    def _lay_bait(self, context: Context, playground: Path) -> None:
        for name in self.BAIT_FILES:
            safe_path(playground, name).write_text(self.BAIT_TEXT, encoding="utf-8")
        self._say_one_of(context, self.BAITED)

    @staticmethod
    def _safe_files(playground: Path, folder: Path) -> list[Path]:
        """Only regular files that really lie inside the playground."""
        files = []
        for path in sorted(folder.iterdir()):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                safe_path(playground, path)
            except OutsidePlayground:
                log.warning("Skipping %s: not inside the playground", path)
                continue
            files.append(path)
        return files
