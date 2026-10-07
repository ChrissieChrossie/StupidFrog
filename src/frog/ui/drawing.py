"""Draws the frog and the speech bubble onto a tkinter canvas."""

from __future__ import annotations

import tkinter as tk

from frog.model import Frog
from frog.pixel_art import HEIGHT, WIDTH, frame_for, runs

WHITE = "#ffffff"
BLACK = "#000000"
BUBBLE_FONT = ("Segoe UI", 10, "bold")
BUBBLE_PADDING = 8
BUBBLE_TAIL = 12

TAG_FROG = "frog"
TAG_BUBBLE = "bubble"


def draw_frog(canvas: tk.Canvas, frog: Frog, center_x: int, ground_y: int, pixel: int) -> None:
    """Redraw the pixel frog. `ground_y` is the height of its feet."""
    canvas.delete(TAG_FROG)
    frame = frame_for(frog.legs_out, frog.direction)
    left = center_x - WIDTH * pixel // 2
    top = ground_y - HEIGHT * pixel - int(frog.height)

    for x, y, length, color in runs(frame):
        x0 = left + x * pixel
        y0 = top + y * pixel
        canvas.create_rectangle(
            x0, y0, x0 + length * pixel, y0 + pixel, fill=color, outline="", tags=TAG_FROG
        )


def draw_speech_bubble(canvas: tk.Canvas, text: str, width: int) -> None:
    """Draw a speech bubble at the top of the window."""
    canvas.delete(TAG_BUBBLE)
    pad = BUBBLE_PADDING
    center = width // 2
    text_id = canvas.create_text(
        center,
        pad + 10,
        text=text,
        width=width - 4 * pad,
        font=BUBBLE_FONT,
        fill=BLACK,
        anchor="n",
        tags=TAG_BUBBLE,
    )
    x0, y0, x1, y1 = canvas.bbox(text_id)
    bubble = canvas.create_rectangle(
        x0 - pad,
        y0 - pad,
        x1 + pad,
        y1 + pad,
        fill=WHITE,
        outline=BLACK,
        width=2,
        tags=TAG_BUBBLE,
    )
    canvas.create_polygon(
        center - 8,
        y1 + pad,
        center + 8,
        y1 + pad,
        center,
        y1 + pad + BUBBLE_TAIL,
        fill=WHITE,
        outline=BLACK,
        width=2,
        tags=TAG_BUBBLE,
    )
    canvas.tag_raise(text_id, bubble)


def clear_speech_bubble(canvas: tk.Canvas) -> None:
    canvas.delete(TAG_BUBBLE)
