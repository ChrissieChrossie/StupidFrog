import pytest

from frog.pixel_art import (
    COLORS,
    HEIGHT,
    JUMPING,
    MOUTH_ROW,
    SITTING,
    WIDTH,
    frame_for,
    mirrored,
    runs,
)


@pytest.mark.parametrize("frame", [SITTING, JUMPING])
def test_frames_have_the_same_size(frame):
    assert len(frame) == HEIGHT
    assert all(len(row) == WIDTH for row in frame)


@pytest.mark.parametrize("frame", [SITTING, JUMPING])
def test_only_known_colors(frame):
    allowed = set(COLORS) | {"."}
    assert {char for row in frame for char in row} <= allowed


def test_walking_left_is_mirrored():
    assert frame_for(jumping=False, direction=1) == SITTING
    assert frame_for(jumping=False, direction=-1) == mirrored(SITTING)
    assert frame_for(jumping=True, direction=1) == JUMPING


def test_mouth_row_is_inside_the_frame():
    assert 0 <= MOUTH_ROW < HEIGHT


def test_runs_merge_equal_pixels():
    assert runs(["KKG.", ".WW."]) == [
        (0, 0, 2, COLORS["K"]),
        (2, 0, 1, COLORS["G"]),
        (1, 1, 2, COLORS["W"]),
    ]


def test_runs_cover_all_pixels():
    drawn = sum(length for _, _, length, _ in runs(SITTING))
    visible = sum(char != "." for row in SITTING for char in row)
    assert drawn == visible
