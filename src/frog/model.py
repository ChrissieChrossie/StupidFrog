"""The frog as a plain data model. No tkinter, so it is easy to test."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto

# Share of each jump spent crouching on the ground before take-off.
GROUND_SHARE = 0.3


class State(Enum):
    WALKING = auto()
    SITTING = auto()  # Waits until `start_walking()` is called (e.g. during an action)
    RESTING = auto()  # Sits still for a while, then hops on by itself
    LEAVING = auto()  # Hops off the screen to take a break
    AWAY = auto()  # Off screen; comes back by itself when the break is over
    RETURNING = auto()  # Hops back onto the screen


MOVING_STATES = frozenset({State.WALKING, State.LEAVING, State.RETURNING})


@dataclass
class Frog:
    x: float
    speed: float  # Pixels per second, on average
    jump_height: float = 40.0  # Pixels
    jumps_per_second: float = 1.5
    direction: int = 1  # 1 = right, -1 = left
    state: State = State.WALKING
    phase: float = 0.0  # 0..1, progress within the current jump
    rest_left_s: float = 0.0
    away_left_s: float = 0.0

    @property
    def airborne(self) -> bool:
        return self.state in MOVING_STATES and self.phase >= GROUND_SHARE

    @property
    def height(self) -> float:
        """Current height above the ground, following a sine arc."""
        if not self.airborne:
            return 0.0
        t = (self.phase - GROUND_SHARE) / (1 - GROUND_SHARE)
        return math.sin(math.pi * t) * self.jump_height

    def step(self, dt: float, min_x: float, max_x: float, margin: float = 0.0) -> bool:
        """Advance the frog by `dt` seconds, turning around at the edges.

        `margin` is how far beyond `min_x`/`max_x` the frog is fully off screen.
        Returns True if the frog has just landed from a jump.
        """
        if self.state is State.RESTING:
            self.rest_left_s -= dt
            if self.rest_left_s <= 0:
                self.start_walking()
            return False
        if self.state is State.AWAY:
            self.away_left_s -= dt
            if self.away_left_s <= 0:
                self._reenter(min_x, max_x, margin)
            return False
        if self.state not in MOVING_STATES:
            return False

        new_phase = self.phase + dt * self.jumps_per_second
        landed = new_phase >= 1.0
        self.phase = new_phase % 1.0
        if not self.airborne:
            return landed  # No horizontal movement while on the ground

        # Move faster in the air so the average speed matches `speed`.
        self.x += self.direction * self.speed * dt / (1 - GROUND_SHARE)
        if self.state is State.WALKING:
            self._bounce(min_x, max_x)
        elif self.state is State.LEAVING:
            if self.x < min_x - margin or self.x > max_x + margin:
                self.state = State.AWAY
                self.phase = 0.0
        elif min_x <= self.x <= max_x:  # RETURNING and fully back on screen
            self.state = State.WALKING
        return landed

    def sit(self) -> None:
        self.state = State.SITTING
        self.phase = 0.0  # Land immediately

    def rest(self, seconds: float) -> None:
        """Sit still for a while, then continue hopping automatically."""
        self.state = State.RESTING
        self.phase = 0.0
        self.rest_left_s = seconds

    def leave(self, break_seconds: float) -> None:
        """Hop off the screen in the current direction and stay away for a while."""
        self.state = State.LEAVING
        self.away_left_s = break_seconds

    def start_walking(self) -> None:
        self.state = State.WALKING
        self.rest_left_s = 0.0

    def turn_around(self) -> None:
        self.direction *= -1

    def _bounce(self, min_x: float, max_x: float) -> None:
        if self.x <= min_x:
            self.x = min_x
            self.direction = 1
        elif self.x >= max_x:
            self.x = max_x
            self.direction = -1

    def _reenter(self, min_x: float, max_x: float, margin: float) -> None:
        """Come back from the side the frog left through."""
        if self.direction > 0:
            self.x, self.direction = max_x + margin, -1
        else:
            self.x, self.direction = min_x - margin, 1
        self.state = State.RETURNING
        self.phase = 0.0
