"""Windows implementation of the foreground window tracker."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging

from .tracker import ActiveWindow, BaseTracker

logger = logging.getLogger(__name__)


class WindowsTracker(BaseTracker):
    """Track active window on Windows using win32 APIs via ctypes."""

    def get_active_window(self) -> ActiveWindow | None:
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return None

            # Get window title
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value

            # Get process ID
            pid = ctypes.wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pid_val = pid.value

            # Get process name
            exe_name = self._get_process_name(pid_val)
            app_name = self._friendly_name(exe_name, title)

            return ActiveWindow(
                app_name=app_name,
                exe_name=exe_name,
                window_title=title,
                pid=pid_val,
            )
        except Exception:
            logger.debug("Failed to get active window", exc_info=True)
            return None

    def get_idle_seconds(self) -> float:
        try:

            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_uint),
                    ("dwTime", ctypes.c_uint),
                ]

            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                return millis / 1000.0
            return 0.0
        except Exception:
            return 0.0

    def _get_process_name(self, pid: int) -> str:
        try:
            import psutil

            proc = psutil.Process(pid)
            return proc.name()
        except Exception:
            return "Unknown"

    def _friendly_name(self, exe_name: str, title: str) -> str:
        """Convert exe name to a friendly app name."""
        name_map = {
            "Code.exe": "Visual Studio Code",
            "chrome.exe": "Google Chrome",
            "firefox.exe": "Firefox",
            "msedge.exe": "Microsoft Edge",
            "WindowsTerminal.exe": "Windows Terminal",
            "explorer.exe": "File Explorer",
            "Discord.exe": "Discord",
            "Slack.exe": "Slack",
            "spotify.exe": "Spotify",
        }
        return name_map.get(exe_name, exe_name.replace(".exe", ""))
