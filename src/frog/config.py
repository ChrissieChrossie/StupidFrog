"""All tunable values in one place."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

# Folder that holds `sounds/`. In the single-file .exe (PyInstaller) the files
# are unpacked into a temporary folder named in `sys._MEIPASS`.
RESOURCES = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


@dataclass(frozen=True)
class Settings:
    # Window
    window_width: int = 240
    window_height: int = 240
    bottom_margin: int = 48  # Room for the taskbar when the work area is unknown (not Windows)
    transparent_color: str = "#ff00ff"  # This color is rendered fully transparent

    # Movement
    frames_per_second: int = 30
    speed: float = 80.0  # Pixels per second, on average
    jump_height: float = 40.0  # Pixels
    jumps_per_second: float = 1.5
    rest_chance: float = 0.12  # Chance to sit down after each landing
    rest_min_s: float = 3.0
    rest_max_s: float = 9.0

    # Appearance
    pixel_size: int = 6  # Screen pixels per pixel-art pixel
    tongue_color: str = "#e8506e"
    tongue_width: int = 10

    # Behaviour
    action_pause_min_s: float = 10.0
    action_pause_max_s: float = 40.0
    ai_pause_factor: float = 1.0  # Pause multiplier while AI quips are active (0.5 = half)
    speech_bubble_s: float = 4.0
    break_min_s: float = 45.0  # How long the frog stays away when it takes a break
    break_max_s: float = 90.0
    reminder_interval_min: float = 60.0  # "Drink something!" and the like
    chase_radius: int = 180  # The frog reacts when the mouse comes this close (pixels)
    chase_cooldown_s: float = 20.0  # Minimum time between two reactions to the mouse

    # Sound
    sound_enabled: bool = True  # Initial value; the context menu remembers the user's choice
    sound_file: Path = field(default_factory=lambda: RESOURCES / "sounds" / "frog-sound.mp3")
    sound_duration_ms: int = 1000  # Only play the start; the file is 8 seconds long

    # Quips from Claude (needs ANTHROPIC_API_KEY, otherwise the built-in list is used)
    ai_quips_enabled: bool = True  # Initial value; the context menu remembers the user's choice
    ai_model: str = "claude-haiku-4-5"

    # The ONLY folder in which the frog may touch files.
    playground: Path = field(default_factory=lambda: Path.home() / "Frosch-Spielwiese")
