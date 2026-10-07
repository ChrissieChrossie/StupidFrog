"""Where the frog may walk: the bottom edge of every monitor."""

from __future__ import annotations

from dataclasses import dataclass

from frog import windows

Rect = tuple[int, int, int, int]  # (left, top, right, bottom)


@dataclass(frozen=True)
class Monitor:
    area: Rect  # The whole monitor
    work: Rect  # Without the taskbar


class Screens:
    """All monitors side by side. The frog walks along the bottom of their work areas."""

    def __init__(self, monitors: list[Monitor]):
        if not monitors:
            raise ValueError("At least one monitor is needed")
        self.monitors = monitors

    @classmethod
    def detect(cls, width: int, height: int, bottom_margin: int, system=windows) -> Screens:
        """Ask Windows for the monitors; elsewhere assume one screen of the given size."""
        found = [Monitor(area, work) for area, work in system.monitors()]
        if not found:
            found = [Monitor((0, 0, width, height), (0, 0, width, height - bottom_margin))]
        return cls(found)

    @property
    def left(self) -> int:
        return min(m.work[0] for m in self.monitors)

    @property
    def right(self) -> int:
        return max(m.work[2] for m in self.monitors)

    @property
    def bounds(self) -> Rect:
        """The rectangle around all monitors."""
        return (
            min(m.area[0] for m in self.monitors),
            min(m.area[1] for m in self.monitors),
            max(m.area[2] for m in self.monitors),
            max(m.area[3] for m in self.monitors),
        )

    def ground_at(self, x: float) -> int:
        """Screen y of the ground at `x`.

        If monitors are stacked, the frog walks on the lowest one.
        Between monitors (a gap in the layout) the nearest monitor counts.
        """
        below = [m for m in self.monitors if m.work[0] <= x < m.work[2]]
        if below:
            return max(m.work[3] for m in below)
        nearest = min(self.monitors, key=lambda m: min(abs(x - m.work[0]), abs(x - m.work[2])))
        return nearest.work[3]
