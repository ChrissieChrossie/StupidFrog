"""Guard: the frog may only touch files inside its playground folder."""

from __future__ import annotations

from pathlib import Path


class OutsidePlayground(PermissionError):
    """A path does not lie inside the playground."""


def safe_path(playground: Path, path: Path | str) -> Path:
    """Return the resolved path if it lies INSIDE the playground, otherwise raise.

    Relative paths are taken relative to the playground. Tricks such as `..`
    or links pointing outside are caught because the check uses `resolve()`.
    """
    base = Path(playground).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()

    if target != base and base not in target.parents:
        raise OutsidePlayground(f"Refusing to touch {target}: not inside {base}")
    return target
