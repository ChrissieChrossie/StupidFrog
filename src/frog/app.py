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
from frog.pixel_art import HEIGHT, MOUTH_ROW
from frog.quips import QuipPicker
from frog.sound import Sound
from frog.ui.drawing import clear_speech_bubble, draw_frog, draw_speech_bubble
from frog.ui.window import FrogWindow, MenuSwitch

log = logging.getLogger(__name__)

RESUME_AFTER_ACTION_MS = 2000
# Random actions only happen while the frog is visible and not busy.
STATES_FOR_ACTIONS = frozenset({State.WALKING, State.RESTING})


class FrogApp:
    """The main loop. Also implements the `Context` that actions use."""

    def __init__(self, settings: Settings, rng: random.Random | None = None):
        self.settings = settings
        self.rng = rng or random.Random()
        self.window = FrogWindow(settings)
        self.frog = Frog(
            x=0,
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
        self.actions = all_actions(self.quips)
        saved_pranks = saved.get("pranks", {})
        for action in self._pranks():
            action.enabled = saved_pranks.get(action.setting_key, True)

        self._last_tick = time.monotonic()
        self._next_action_at = self._last_tick + self._random_pause()
        self._bubble_job: str | None = None

        self.window.on_left_click(lambda: self.say(self.quips.next_quip()))
        self.window.build_menu(
            switches=[
                MenuSwitch("Sprüche von Claude", self.quips.enabled, self.toggle_ai),
                MenuSwitch("Quak-Ton", self.sound.enabled, self.toggle_sound),
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
        s = self.settings
        mouth_x = int(self.frog.x) + s.window_width // 2
        mouth_y = self.window.top_y + s.window_height - (HEIGHT - MOUTH_ROW) * s.pixel_size
        self.frog.direction = 1 if x >= mouth_x else -1
        self.window.tongue((mouth_x, mouth_y), (x, y), on_hit)

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

    def _tick(self) -> None:
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now
        s = self.settings

        max_x = self.window.screen_width - s.window_width
        landed = self.frog.step(dt, 0, max_x, margin=s.window_width)
        if landed and self.rng.random() < s.rest_chance:
            self.frog.rest(self.rng.uniform(s.rest_min_s, s.rest_max_s))

        if now >= self._next_action_at:
            if self.frog.state in STATES_FOR_ACTIONS:
                self._run_random_action()
            self._next_action_at = now + self._random_pause()

        self.window.move_to(self.frog.x)
        draw_frog(self.window.canvas, self.frog, s.window_width // 2, s.window_height, s.pixel_size)
        self.window.later(1000 // s.frames_per_second, self._tick)

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
