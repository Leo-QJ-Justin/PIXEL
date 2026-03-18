"""Linux implementation of the foreground window tracker (X11 only)."""

from __future__ import annotations

import logging
import subprocess

from .tracker import ActiveWindow, BaseTracker

logger = logging.getLogger(__name__)


class LinuxTracker(BaseTracker):
    """Track active window on Linux using X11 (xdotool/xprop).

    Note: This does NOT work on Wayland. X11 or XWayland is required.
    """

    def get_active_window(self) -> ActiveWindow | None:
        try:
            # Get active window ID
            wid = (
                subprocess.check_output(["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL)
                .decode()
                .strip()
            )
            if not wid:
                return None

            # Get window PID
            pid_str = (
                subprocess.check_output(["xdotool", "getwindowpid", wid], stderr=subprocess.DEVNULL)
                .decode()
                .strip()
            )
            pid = int(pid_str) if pid_str else 0

            # Get window name
            title = (
                subprocess.check_output(
                    ["xdotool", "getwindowname", wid], stderr=subprocess.DEVNULL
                )
                .decode()
                .strip()
            )

            # Get process name from /proc
            exe_name = "Unknown"
            if pid:
                try:
                    with open(f"/proc/{pid}/comm") as f:
                        exe_name = f.read().strip()
                except (FileNotFoundError, PermissionError):
                    pass

            return ActiveWindow(
                app_name=exe_name,
                exe_name=exe_name,
                window_title=title,
                pid=pid,
            )
        except FileNotFoundError:
            logger.warning("xdotool not found — install it for Linux screen time tracking")
            return None
        except Exception:
            logger.debug("Failed to get active window on Linux", exc_info=True)
            return None

    def get_idle_seconds(self) -> float:
        try:
            output = (
                subprocess.check_output(["xprintidle"], stderr=subprocess.DEVNULL).decode().strip()
            )
            return int(output) / 1000.0
        except FileNotFoundError:
            logger.warning(
                "xprintidle not found — idle detection disabled (install xprintidle for accurate tracking)"
            )
            return 0.0
        except Exception:
            return 0.0
