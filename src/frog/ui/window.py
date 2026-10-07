"""A borderless, transparent window that always stays on top.

All texts in this module are shown to the user, therefore they are German.
"""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from frog.config import Settings

log = logging.getLogger(__name__)

Point = tuple[int, int]
UI_FONT = ("Segoe UI", 11)
TAG_TONGUE = "tongue"


@dataclass
class MenuSwitch:
    """A checkbox entry in the context menu."""

    label: str
    on: bool
    on_toggle: Callable[[bool], None]


class FrogWindow:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.root = tk.Tk()
        self.root.title("Frosch")
        self.root.overrideredirect(True)  # No border, no title bar
        self.root.attributes("-topmost", True)

        color = settings.transparent_color
        self.root.configure(bg=color)
        try:
            # Windows only: this color becomes fully transparent.
            self.root.attributes("-transparentcolor", color)
        except tk.TclError:
            log.warning("Transparent windows are not supported here; the background stays visible.")

        self.canvas = tk.Canvas(
            self.root,
            width=settings.window_width,
            height=settings.window_height,
            bg=color,
            highlightthickness=0,
        )
        self.canvas.pack()
        self._menu_vars: list[tk.BooleanVar] = []  # Keep references so tkinter keeps them

    @property
    def screen_size(self) -> Point:
        """Size of the primary screen. Only used when the monitors are unknown."""
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def move_to(self, x: float, y: float) -> None:
        s = self.settings
        self.root.geometry(f"{s.window_width}x{s.window_height}+{int(x)}+{int(y)}")

    def pointer(self) -> Point:
        """Current mouse position in screen coordinates."""
        return self.root.winfo_pointerxy()

    def on_mouse(
        self,
        press: Callable[[int, int], None],
        drag: Callable[[int, int], None],
        release: Callable[[int, int], None],
    ) -> None:
        """Left mouse button events on the frog, in screen coordinates."""
        self.canvas.bind("<ButtonPress-1>", lambda e: press(e.x_root, e.y_root))
        self.canvas.bind("<B1-Motion>", lambda e: drag(e.x_root, e.y_root))
        self.canvas.bind("<ButtonRelease-1>", lambda e: release(e.x_root, e.y_root))

    def build_menu(
        self,
        switches: list[MenuSwitch],
        pranks: list[MenuSwitch],
        on_personality: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        """Right-click menu: switches, a "Streiche" submenu, personality and quit."""
        menu = tk.Menu(self.root, tearoff=0)
        for switch in switches:
            self._add_switch(menu, switch)

        prank_menu = tk.Menu(menu, tearoff=0)
        for switch in pranks:
            self._add_switch(prank_menu, switch)
        menu.add_cascade(label="Streiche", menu=prank_menu)

        menu.add_command(label="Charakter beschreiben ...", command=on_personality)
        menu.add_separator()
        menu.add_command(label="Tschüss (beenden)", command=on_quit)
        self.canvas.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _add_switch(self, menu: tk.Menu, switch: MenuSwitch) -> None:
        var = tk.BooleanVar(master=self.root, value=switch.on)
        self._menu_vars.append(var)
        menu.add_checkbutton(
            label=switch.label,
            variable=var,
            command=lambda: switch.on_toggle(var.get()),
        )

    def personality_dialog(self, text: str, on_save: Callable[[str], None]) -> None:
        """Small dialog in which the user describes the frog's personality."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Charakter vom Frosch")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)

        tk.Label(
            dialog,
            text="Wie soll dein Frosch sein? Beschreib ihn in ein paar Sätzen.",
            font=UI_FONT,
            justify="left",
        ).pack(padx=12, pady=(12, 6), anchor="w")

        entry = tk.Text(dialog, width=50, height=8, wrap="word", font=UI_FONT)
        entry.insert("1.0", text)
        entry.pack(padx=12)
        entry.focus_set()

        def save() -> None:
            on_save(entry.get("1.0", "end").strip())
            dialog.destroy()

        buttons = tk.Frame(dialog)
        buttons.pack(padx=12, pady=12, anchor="e")
        tk.Button(buttons, text="Abbrechen", command=dialog.destroy).pack(side="right")
        tk.Button(buttons, text="Speichern", command=save).pack(side="right", padx=6)

    def tongue(
        self,
        start: Point,
        target: Point,
        on_hit: Callable[[], None],
        bounds: tuple[int, int, int, int],
        steps: int = 8,
        ms_per_step: int = 30,
    ) -> None:
        """Animate a tongue across the screen from `start` to `target`.

        A transparent overlay covering `bounds` (all monitors) is shown briefly.
        Clicks pass straight through its transparent parts.
        """
        s = self.settings
        try:
            overlay = tk.Toplevel(self.root)
            overlay.overrideredirect(True)
            overlay.attributes("-topmost", True)
            overlay.attributes("-transparentcolor", s.transparent_color)
        except tk.TclError:
            log.warning("Tongue overlay not supported here; pressing the button directly.")
            on_hit()
            return
        left, top, right, bottom = bounds
        width, height = right - left, bottom - top
        # Monitors left of or above the main one have negative coordinates.
        overlay.geometry(f"{width}x{height}+{left}+{top}")
        start = (start[0] - left, start[1] - top)
        target = (target[0] - left, target[1] - top)
        canvas = tk.Canvas(
            overlay, width=width, height=height, bg=s.transparent_color, highlightthickness=0
        )
        canvas.pack()

        def draw(progress: float) -> None:
            canvas.delete(TAG_TONGUE)
            x = start[0] + (target[0] - start[0]) * progress
            y = start[1] + (target[1] - start[1]) * progress
            r = s.tongue_width
            canvas.create_line(
                *start, x, y, fill=s.tongue_color, width=r, capstyle="round", tags=TAG_TONGUE
            )
            canvas.create_oval(
                x - r, y - r, x + r, y + r, fill=s.tongue_color, outline="", tags=TAG_TONGUE
            )

        # Out (1 .. steps), then back in (steps - 1 .. 0).
        frames = list(range(1, steps + 1)) + list(range(steps - 1, -1, -1))
        hit_frame = steps - 1

        def animate(i: int = 0) -> None:
            if i >= len(frames):
                overlay.destroy()
                return
            draw(frames[i] / steps)
            if i == hit_frame:
                try:
                    on_hit()
                except Exception:
                    log.exception("Tongue hit handler failed")
            self.root.after(ms_per_step, animate, i + 1)

        animate()

    def later(self, milliseconds: int, task: Callable[[], None]) -> str:
        return self.root.after(milliseconds, task)

    def cancel(self, job: str) -> None:
        self.root.after_cancel(job)

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        self.root.destroy()
