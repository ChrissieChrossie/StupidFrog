"""Ties model, actions and window together into a running app.

Lines the frog says are shown to the user, therefore they are German.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

from frog import storage
from frog.actions import Action, all_actions, pick_action
from frog.ai_quips import DEFAULT_PERSONALITY, AiQuipSource, ai_available
from frog.config import Settings
from frog.model import Frog, State
from frog.pixel_art import HEIGHT, MOUTH_ROW, WIDTH
from frog.quips import QuipPicker
from frog.reactions import DROPPED, FLED, PICKED_UP, SNAPPED, MouseChase, Reaction, Reminders
from frog.screens import Screens
from frog.sound import Sound
from frog.ui.drawing import clear_speech_bubble, draw_frog, draw_speech_bubble
from frog.ui.window import FrogWindow, MenuSwitch

log = logging.getLogger(__name__)

RESUME_AFTER_ACTION_MS = 2000
DRAG_THRESHOLD = 6  # Pixels the mouse must move before a click becomes a drag
GRAB_PADDING = 10  # Pixels around the frog that still count as "on the frog"
SCREENS_REFRESH_S = 30.0  # Monitors can be plugged in or out while the frog runs
# Random actions and reactions only happen while the frog is visible and not busy.
STATES_FOR_ACTIONS = frozenset({State.WALKING, State.RESTING})


class FrogApp:
    """The main loop. Also implements the `Context` that actions use."""

    def __init__(self, settings: Settings, rng: random.Random | None = None):
        self.settings = settings
        self.rng = rng or random.Random()
        self.window = FrogWindow(settings)
        self.screens = self._detect_screens()
        self.frog = Frog(
            x=self.screens.left,
            speed=settings.speed,
            jump_height=settings.jump_height,
            jumps_per_second=settings.jumps_per_second,
        )

        saved = storage.load()
        self.quips = AiQuipSource(
            fallback=QuipPicker(rng=self.rng),
            model=settings.ai_model,
            enabled=saved.get("ai_quips", settings.ai_quips_enabled),
            personality=saved.get("personality", ""),
        )
        self.sound = Sound(
            settings.sound_file,
            settings.sound_duration_ms,
            enabled=saved.get("sound", settings.sound_enabled),
        )
        self.chase = MouseChase(
            settings.chase_radius,
            settings.chase_cooldown_s,
            enabled=saved.get("chase_mouse", True),
            rng=self.rng,
        )
        self._last_tick = time.monotonic()
        self.reminders = Reminders(
            settings.reminder_interval_min * 60,
            now=self._last_tick,
            enabled=saved.get("reminders", True),
            rng=self.rng,
        )
        self.actions = all_actions(self.quips)
        saved_pranks = saved.get("pranks", {})
        for action in self._pranks():
            action.enabled = saved_pranks.get(action.setting_key, True)

        self._next_action_at = self._last_tick + self._random_pause()
        self._screens_checked_at = self._last_tick
        self._bubble_job: str | None = None
        self._window_y = 0
        self._press: tuple[int, int] | None = None  # Where the left button went down
        self._grab_offset = (0, 0)  # Pointer position relative to the window's corner
        self._dragging = False

        self.window.on_mouse(self._on_press, self._on_drag, self._on_release)
        self.window.build_menu(
            switches=[
                MenuSwitch("Sprüche von Claude", self.quips.enabled, self.toggle_ai),
                MenuSwitch("Quak-Ton", self.sound.enabled, self.toggle_sound),
                MenuSwitch("Maus jagen", self.chase.enabled, self.toggle_chase),
                MenuSwitch("Erinnerungen", self.reminders.enabled, self.toggle_reminders),
            ],
            pranks=[
                MenuSwitch(action.name, action.enabled, self._prank_toggler(action))
                for action in self._pranks()
            ],
            on_personality=self.edit_personality,
            on_quit=self.quit,
        )

    # --- Context for actions --------------------------------------------------

    def say(self, text: str) -> None:
        log.debug("Frog says: %s", text)
        draw_speech_bubble(self.window.canvas, text, self.settings.window_width)
        self.sound.play()
        if self._bubble_job:
            self.window.cancel(self._bubble_job)
        duration_ms = int(self.settings.speech_bubble_s * 1000)
        self._bubble_job = self.window.later(duration_ms, self._clear_bubble)

    def later(self, milliseconds: int, task: Callable[[], None]) -> str:
        return self.window.later(milliseconds, task)

    def tongue(self, x: int, y: int, on_hit: Callable[[], None]) -> None:
        mouth = self._mouth()
        self.frog.direction = 1 if x >= mouth[0] else -1
        self.window.tongue(mouth, (x, y), on_hit, self.screens.bounds)

    # --- Menu callbacks -------------------------------------------------------

    def toggle_prank(self, action: Action, on: bool) -> None:
        action.enabled = on
        pranks = {**storage.load().get("pranks", {}), action.setting_key: on}
        storage.update(pranks=pranks)
        if not on:
            action.cleanup()
            self.say(f"Okay, okay. {action.name}: aus.")
        elif action.can_run():
            self.say(f"{action.name}: an! Hihi.")
        else:
            self.say("Das klappt nur unter Windows.")

    def toggle_sound(self, on: bool) -> None:
        self.sound.enabled = on
        storage.update(sound=on)
        self.say("Quak! Hörst du mich?" if on else "Na gut, ich bin still. Fast.")

    def toggle_ai(self, on: bool) -> None:
        self.quips.enabled = on
        storage.update(ai_quips=on)
        if not on:
            self.say("KI aus. Ich nehm wieder meine alten Sprüche.")
            return
        available, reason = ai_available()
        if available:
            self.quips.prefetch()
            self.say("KI an! Jetzt wird's richtig frech.")
        else:
            log.warning("AI quips unavailable: %s", reason)
            self.say("Mir fehlt der Schlüssel. Schau in die README.")

    def toggle_chase(self, on: bool) -> None:
        self.chase.enabled = on
        storage.update(chase_mouse=on)
        self.say("Na warte, Mauszeiger!" if on else "Okay, ich lass die Maus in Ruhe.")

    def toggle_reminders(self, on: bool) -> None:
        self.reminders.enabled = on
        storage.update(reminders=on)
        if on:
            self.reminders.restart(time.monotonic())
            self.say("Ich pass auf dich auf. Ob du willst oder nicht.")
        else:
            self.say("Gut, dann vertrock halt.")

    def edit_personality(self) -> None:
        text = self.quips.personality or DEFAULT_PERSONALITY
        self.window.personality_dialog(text, self.save_personality)

    def save_personality(self, personality: str) -> None:
        self.quips.set_personality(personality)
        storage.update(personality=self.quips.personality)
        if self.quips.active:
            self.say("Gemerkt! Ich bin jetzt ein ganz neuer Frosch.")
        else:
            self.say("Gemerkt! Damit ich so rede, muss die KI an sein.")

    # --- Lifecycle ------------------------------------------------------------

    def run(self) -> None:
        log.info("Frog starting. Right-click the frog to open the menu.")
        if self.quips.enabled:
            available, reason = ai_available()
            log.info("AI quips: %s", "on" if available else f"off ({reason})")
        self.quips.prefetch()
        self.say("Hallo! Ich bin da.")
        self._tick()
        self.window.run()

    def quit(self) -> None:
        log.info("Frog hopping off.")
        for action in self.actions:
            try:
                action.cleanup()
            except Exception:
                log.exception("Cleanup of %r failed", action.name)
        self.sound.close()
        self.window.close()

    # --- Internals ------------------------------------------------------------

    def _pranks(self) -> list[Action]:
        return [action for action in self.actions if action.setting_key]

    def _prank_toggler(self, action: Action) -> Callable[[bool], None]:
        return lambda on: self.toggle_prank(action, on)

    def _detect_screens(self) -> Screens:
        s = self.settings
        width, height = self.window.screen_size
        return Screens.detect(width, height, s.bottom_margin)

    def _tick(self) -> None:
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now
        s = self.settings

        if now - self._screens_checked_at >= SCREENS_REFRESH_S:
            self.screens = self._detect_screens()
            self._screens_checked_at = now

        min_x = self.screens.left
        max_x = self.screens.right - s.window_width
        was_falling = self.frog.state is State.FALLING
        landed = self.frog.step(dt, min_x, max_x, margin=s.window_width)
        if landed and was_falling:
            self.say(self.rng.choice(DROPPED))
        elif landed and self.rng.random() < s.rest_chance:
            self.frog.rest(self.rng.uniform(s.rest_min_s, s.rest_max_s))

        if self.frog.state in STATES_FOR_ACTIONS:
            self._react_to_user(now)
        if now >= self._next_action_at:
            if self.frog.state in STATES_FOR_ACTIONS:
                self._run_random_action()
            self._next_action_at = now + self._random_pause()

        self._render()
        self.window.later(1000 // s.frames_per_second, self._tick)

    def _render(self) -> None:
        s = self.settings
        ground = self.screens.ground_at(self.frog.x + s.window_width / 2)
        self._window_y = int(ground - s.window_height - self.frog.lift)
        self.window.move_to(self.frog.x, self._window_y)
        draw_frog(self.window.canvas, self.frog, s.window_width // 2, s.window_height, s.pixel_size)

    def _mouth(self) -> tuple[int, int]:
        """Screen position of the frog's mouth."""
        s = self.settings
        mouth_x = int(self.frog.x) + s.window_width // 2
        mouth_y = self._window_y + s.window_height - (HEIGHT - MOUTH_ROW) * s.pixel_size
        return mouth_x, mouth_y

    def _react_to_user(self, now: float) -> None:
        line = self.reminders.due(now)
        if line:
            self.say(line)
            return

        pointer = self.window.pointer()
        mouth = self._mouth()
        reaction = self.chase.react(now, mouth, pointer, self._is_on_frog(pointer))
        if reaction is Reaction.SNAP:
            self.say(self.rng.choice(SNAPPED))
            self.tongue(*pointer, lambda: None)
        elif reaction is Reaction.FLEE:
            self.frog.direction = -1 if pointer[0] > mouth[0] else 1
            self.frog.start_walking()
            self.say(self.rng.choice(FLED))

    def _is_on_frog(self, point: tuple[int, int]) -> bool:
        """True if `point` is on the frog itself (not just somewhere in its window)."""
        s = self.settings
        half_width = WIDTH * s.pixel_size // 2 + GRAB_PADDING
        center_x = self.frog.x + s.window_width // 2
        bottom = self._window_y + s.window_height
        top = bottom - HEIGHT * s.pixel_size - GRAB_PADDING
        return abs(point[0] - center_x) <= half_width and top <= point[1] <= bottom

    # --- Mouse: click to talk, drag to pick up ----------------------------------

    def _on_press(self, x: int, y: int) -> None:
        self._press = (x, y)
        self._grab_offset = (x - int(self.frog.x), y - self._window_y)
        self._dragging = False

    def _on_drag(self, x: int, y: int) -> None:
        if self._press is None:
            return
        if not self._dragging:
            moved = max(abs(x - self._press[0]), abs(y - self._press[1]))
            if moved < DRAG_THRESHOLD or self.frog.state is State.AWAY:
                return
            self._dragging = True
            self.frog.pick_up()
            self.say(self.rng.choice(PICKED_UP))

        s = self.settings
        new_x = x - self._grab_offset[0]
        top = y - self._grab_offset[1]
        ground = self.screens.ground_at(new_x + s.window_width / 2)
        self.frog.hold_at(new_x, ground - s.window_height - top)
        self._render()

    def _on_release(self, _x: int, _y: int) -> None:
        if self._dragging:
            self.frog.drop()
        elif self._press is not None:
            self.say(self.quips.next_quip())
        self._press = None
        self._dragging = False

    def _run_random_action(self) -> None:
        action = pick_action(self.actions, self.rng)
        if action is None:
            return
        log.debug("Action: %s", action.name)
        self.frog.sit()
        try:
            action.run(self)
        except Exception:
            # A broken action must never crash the whole frog.
            log.exception("Action %r failed", action.name)
        self.window.later(RESUME_AFTER_ACTION_MS, self._resume_after_action)

    def _resume_after_action(self) -> None:
        # Actions such as taking a break change the state themselves; leave those alone.
        if self.frog.state is State.SITTING:
            self.frog.start_walking()

    def _random_pause(self) -> float:
        s = self.settings
        pause = self.rng.uniform(s.action_pause_min_s, s.action_pause_max_s)
        return pause * s.ai_pause_factor if self.quips.active else pause

    def _clear_bubble(self) -> None:
        clear_speech_bubble(self.window.canvas)
        self._bubble_job = None
