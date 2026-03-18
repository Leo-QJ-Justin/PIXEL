"""Cross-platform foreground window tracker abstraction."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ActiveWindow:
    """Represents the currently focused window."""

    app_name: str  # Human-readable (e.g., "Visual Studio Code")
    exe_name: str  # Process name (e.g., "Code.exe")
    window_title: str  # Window title
    pid: int


class BaseTracker(ABC):
    """Abstract base for platform-specific window trackers."""

    @abstractmethod
    def get_active_window(self) -> ActiveWindow | None:
        """Return the currently focused window, or None if unable to determine."""
        ...

    @abstractmethod
    def get_idle_seconds(self) -> float:
        """Return seconds since last user input (mouse/keyboard)."""
        ...


class UnsupportedPlatformError(RuntimeError):
    pass


def create_tracker() -> BaseTracker:
    """Factory that returns the correct tracker for the current platform."""
    if sys.platform == "win32":
        from .tracker_windows import WindowsTracker

        return WindowsTracker()
    elif sys.platform == "darwin":
        from .tracker_macos import MacOSTracker

        return MacOSTracker()
    elif sys.platform.startswith("linux"):
        from .tracker_linux import LinuxTracker

        return LinuxTracker()
    else:
        raise UnsupportedPlatformError(f"Screen time tracking not supported on {sys.platform}")
