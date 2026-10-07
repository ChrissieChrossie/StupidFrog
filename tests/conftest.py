from dataclasses import dataclass, field

import pytest

from frog.config import Settings
from frog.model import Frog


@dataclass
class FakeContext:
    """Stands in for the app: records what actions say and schedule."""

    settings: Settings = field(default_factory=Settings)
    frog: Frog = field(default_factory=lambda: Frog(x=0, speed=10))
    said: list[str] = field(default_factory=list)
    scheduled: list = field(default_factory=list)
    licked: list = field(default_factory=list)

    def say(self, text):
        self.said.append(text)

    def later(self, milliseconds, task):
        self.scheduled.append(task)

    def tongue(self, x, y, on_hit):
        self.licked.append((x, y))
        on_hit()  # The tongue hits immediately


@pytest.fixture
def context(tmp_path):
    return FakeContext(Settings(playground=tmp_path / "Frosch-Spielwiese"))
