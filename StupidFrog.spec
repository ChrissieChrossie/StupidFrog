# PyInstaller build recipe for the single-file StupidFrog.exe.
# Build with build.bat, or: python -m PyInstaller --noconfirm --clean StupidFrog.spec

from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ["src/frog/__main__.py"],
    pathex=["src"],
    datas=[("src/sounds/frog-sound.mp3", "sounds")],
    # Imported lazily inside functions, so list it explicitly.
    hiddenimports=collect_submodules("anthropic"),
    excludes=["pytest", "ruff"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="StupidFrog",
    console=False,  # No black console window next to the frog
    upx=False,  # Packed executables are flagged by virus scanners more often
)
