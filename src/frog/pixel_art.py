"""The frog as pixel art. No tkinter, so it is easy to test.

Traced pixel by pixel from Christopher's template.
Each frame is a list of rows; each character is one pixel:
    .  transparent       K  dark outline      G  green
    W  white (eyes)      C  belly (light)     R  pink cheeks
The pupils look to the right. Frames are mirrored for walking left.
"""

from __future__ import annotations

Frame = list[str]

COLORS: dict[str, str] = {
    "K": "#393639",
    "G": "#94bc53",
    "W": "#fdfdfd",
    "C": "#d3f88f",
    "R": "#f7a9c1",
}

_HEAD: Frame = [
    "...KKK....KKK...",
    "..KWWWK..KWWWK..",
    ".KWWKKWKKWWKKWK.",
    ".KWWKKWGGWWKKWK.",
    ".KWWWWWGGWWWWWK.",
    "..KWWWKGGKWWWK..",
    ".KGKKKGGGGKKKGK.",
    "KRRGGGGGGGGGGRRK",
    "KRRGKGGGGGGKGRRK",
    "KGGGGKKKKKKGGGGK",
    ".KGGGGCCCCGGGGK.",
    "..KKCCCCCCCCKK..",
]

SITTING: Frame = _HEAD + [
    ".KGGCCCCCCCCGGK.",
    "KGKGCCCCCCCCGKGK",
    "KGKGKKCCCCKKGKGK",
    "KGKGGGKCCKGGGKGK",
    ".KKKKKKKKKKKKKK.",
]

# While jumping, the legs stretch downwards.
JUMPING: Frame = _HEAD + [
    "..KGCCCCCCCCGK..",
    "..KKCCCCCCCCKK..",
    ".KGK.KKKKKK.KGK.",
    "KGGK........KGGK",
    "KKKK........KKKK",
]

WIDTH = len(SITTING[0])
HEIGHT = len(SITTING)
MOUTH_ROW = 9  # The tongue starts from this row


def mirrored(frame: Frame) -> Frame:
    return [row[::-1] for row in frame]


def frame_for(jumping: bool, direction: int) -> Frame:
    """Pick the sitting or jumping frame, facing the given direction."""
    frame = JUMPING if jumping else SITTING
    return frame if direction > 0 else mirrored(frame)


def runs(frame: Frame) -> list[tuple[int, int, int, str]]:
    """Merge equal neighbouring pixels in a row into runs of (x, y, length, color).

    This keeps the number of rectangles tkinter has to draw small.
    """
    result = []
    for y, row in enumerate(frame):
        x = 0
        while x < len(row):
            char = row[x]
            length = 1
            while x + length < len(row) and row[x + length] == char:
                length += 1
            if char != ".":
                result.append((x, y, length, COLORS[char]))
            x += length
    return result
