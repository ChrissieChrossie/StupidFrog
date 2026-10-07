"""Small Windows helpers built on ctypes (no extra packages needed).

Everything here is harmless and reversible:
- Restore minimized windows.
- Minimize, maximize or restore windows.
- Briefly hide the desktop icons (the app shows them again).
- Move a desktop icon (the app puts it back).
On other systems `is_available()` simply returns False.
"""

from __future__ import annotations

import ctypes
import os
import sys

IS_WINDOWS = sys.platform == "win32"

# Win32 constants
SW_HIDE = 0
SW_MAXIMIZE = 3
SW_SHOW = 5
SW_MINIMIZE = 6
SW_RESTORE = 9
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x80
GW_OWNER = 4
GWL_STYLE = -16
DWMWA_CLOAKED = 14

# List view (desktop icons)
LVM_GETITEMCOUNT = 0x1004
LVM_SETITEMPOSITION = 0x100F
LVM_GETITEMPOSITION = 0x1010
LVS_AUTOARRANGE = 0x0100
ICON_CENTER = (37, 24)  # Rough offset from an icon's top-left corner to its picture

# Reading icon positions needs a small buffer inside Explorer's process.
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
MEM_COMMIT_RESERVE = 0x3000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04

# Caption buttons (estimated for Windows 10/11 at 100 % scaling)
BUTTON_WIDTH = 46
BUTTON_HEIGHT = 30
INVISIBLE_BORDER = 8
BUTTON_OFFSETS = {"maximize": 1.5, "minimize": 2.5}  # In button widths from the right edge

Window = tuple[int, str]  # (handle, title)

dwmapi = None
if IS_WINDOWS:
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsZoomed.argtypes = [wintypes.HWND]
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetWindow.restype = wintypes.HWND
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowW.restype = wintypes.HWND
    user32.FindWindowExW.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
    ]
    user32.FindWindowExW.restype = wintypes.HWND
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = wintypes.LPARAM
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.VirtualAllocEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        ctypes.c_size_t,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    kernel32.VirtualAllocEx.restype = wintypes.LPVOID
    kernel32.VirtualFreeEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        ctypes.c_size_t,
        wintypes.DWORD,
    ]
    kernel32.ReadProcessMemory.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.LPVOID,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]

    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        dwmapi.DwmGetWindowAttribute.argtypes = [
            wintypes.HWND,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
    except OSError:
        dwmapi = None


def is_available() -> bool:
    return IS_WINDOWS


# --- Windows ------------------------------------------------------------------


def _is_cloaked(hwnd) -> bool:
    """Some windows (e.g. background UWP apps) are visible but "cloaked"."""
    if dwmapi is None:
        return False
    value = ctypes.c_int(0)
    dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(value), ctypes.sizeof(value))
    return bool(value.value)


def _is_own(hwnd) -> bool:
    """The frog never touches its own windows."""
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value == os.getpid()


def _app_windows(minimized: bool) -> list[Window]:
    """Normal application windows, without tool windows and without our own."""
    if not IS_WINDOWS:
        return []
    found: list[Window] = []

    @WNDENUMPROC
    def check(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd) or bool(user32.IsIconic(hwnd)) != minimized:
            return True
        if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
            return True
        if user32.GetWindow(hwnd, GW_OWNER) or _is_own(hwnd) or _is_cloaked(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            found.append((hwnd, buffer.value))
        return True

    user32.EnumWindows(check, 0)
    return found


def minimized_windows() -> list[Window]:
    return _app_windows(minimized=True)


def open_windows() -> list[Window]:
    return _app_windows(minimized=False)


def window_exists(hwnd: int) -> bool:
    return IS_WINDOWS and bool(user32.IsWindow(hwnd))


def is_maximized(hwnd: int) -> bool:
    return IS_WINDOWS and bool(user32.IsZoomed(hwnd))


def _show(hwnd: int, command: int) -> None:
    if IS_WINDOWS:
        user32.ShowWindow(hwnd, command)


def restore_window(hwnd: int) -> None:
    _show(hwnd, SW_RESTORE)


def minimize_window(hwnd: int) -> None:
    _show(hwnd, SW_MINIMIZE)


def maximize_window(hwnd: int) -> None:
    _show(hwnd, SW_MAXIMIZE)


def button_position(hwnd: int, button: str) -> tuple[int, int] | None:
    """Approximate screen center of the "minimize" or "maximize" caption button.

    Windows does not expose the exact position easily, so it is estimated:
    the three caption buttons sit at the top right, each about 46 pixels wide.
    """
    if not IS_WINDOWS:
        return None
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    right = rect.right - INVISIBLE_BORDER
    top = rect.top + (INVISIBLE_BORDER if is_maximized(hwnd) else 1)
    return int(right - BUTTON_WIDTH * BUTTON_OFFSETS[button]), int(top + BUTTON_HEIGHT / 2)


# --- Desktop icons --------------------------------------------------------------


def _icon_list_view() -> int | None:
    """Find the list view that holds the desktop icons (SysListView32)."""
    progman = user32.FindWindowW("Progman", None)
    shell_view = user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None)
    if not shell_view:
        # With a slideshow wallpaper the view lives inside a "WorkerW" window.
        worker = None
        while True:
            worker = user32.FindWindowExW(None, worker, "WorkerW", None)
            if not worker:
                break
            shell_view = user32.FindWindowExW(worker, None, "SHELLDLL_DefView", None)
            if shell_view:
                break
    if not shell_view:
        return None
    return user32.FindWindowExW(shell_view, None, "SysListView32", None) or None


Point = tuple[int, int]


class DesktopIcons:
    """Hides, shows and moves the desktop icons."""

    def __init__(self, list_view: int):
        self._list_view = list_view

    @classmethod
    def find(cls) -> DesktopIcons | None:
        if not IS_WINDOWS:
            return None
        list_view = _icon_list_view()
        return cls(list_view) if list_view else None

    def visible(self) -> bool:
        return bool(user32.IsWindowVisible(self._list_view))

    def hide(self) -> None:
        user32.ShowWindow(self._list_view, SW_HIDE)

    def show(self) -> None:
        user32.ShowWindow(self._list_view, SW_SHOW)

    def auto_arranged(self) -> bool:
        """With "Auto arrange icons" on, Windows snaps moved icons straight back."""
        return bool(user32.GetWindowLongW(self._list_view, GWL_STYLE) & LVS_AUTOARRANGE)

    def size(self) -> Point:
        rect = wintypes.RECT()
        user32.GetClientRect(self._list_view, ctypes.byref(rect))
        return rect.right, rect.bottom

    def positions(self) -> list[Point]:
        """Top-left corner of every icon, in list view coordinates.

        The list view belongs to Explorer, so the answer has to be written into
        a small buffer inside Explorer's process and read back from there.
        """
        count = user32.SendMessageW(self._list_view, LVM_GETITEMCOUNT, 0, 0)
        if count <= 0:
            return []
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(self._list_view, ctypes.byref(pid))
        access = PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE
        process = kernel32.OpenProcess(access, False, pid.value)
        if not process:
            return []
        try:
            point = wintypes.POINT()
            size = ctypes.sizeof(point)
            buffer = kernel32.VirtualAllocEx(
                process, None, size, MEM_COMMIT_RESERVE, PAGE_READWRITE
            )
            if not buffer:
                return []
            try:
                found = []
                for index in range(count):
                    user32.SendMessageW(self._list_view, LVM_GETITEMPOSITION, index, buffer)
                    kernel32.ReadProcessMemory(process, buffer, ctypes.byref(point), size, None)
                    found.append((point.x, point.y))
                return found
            finally:
                kernel32.VirtualFreeEx(process, buffer, 0, MEM_RELEASE)
        finally:
            kernel32.CloseHandle(process)

    def move(self, index: int, position: Point) -> None:
        x, y = position
        packed = (y & 0xFFFF) << 16 | (x & 0xFFFF)  # MAKELPARAM
        user32.SendMessageW(self._list_view, LVM_SETITEMPOSITION, index, packed)

    def screen_point(self, position: Point) -> Point:
        """Screen point of the icon picture whose top-left corner is `position`."""
        point = wintypes.POINT(position[0] + ICON_CENTER[0], position[1] + ICON_CENTER[1])
        user32.ClientToScreen(self._list_view, ctypes.byref(point))
        return point.x, point.y
