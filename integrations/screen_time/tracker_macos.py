"""macOS implementation of the foreground window tracker."""

from __future__ import annotations

import logging

from .tracker import ActiveWindow, BaseTracker

logger = logging.getLogger(__name__)


class MacOSTracker(BaseTracker):
    """Track active window on macOS using pyobjc."""

    def get_active_window(self) -> ActiveWindow | None:
        try:
            from AppKit import NSWorkspace

            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if not app:
                return None
            return ActiveWindow(
                app_name=app.localizedName() or "Unknown",
                exe_name=app.bundleIdentifier() or "unknown",
                window_title=app.localizedName() or "",
                pid=app.processIdentifier(),
            )
        except ImportError:
            logger.warning("pyobjc not installed — macOS screen time tracking unavailable")
            return None
        except Exception:
            logger.debug("Failed to get active window on macOS", exc_info=True)
            return None

    def get_idle_seconds(self) -> float:
        try:
            from Quartz import (
                CGEventSourceSecondsSinceLastEventType,
                kCGAnyInputEventType,
                kCGEventSourceStateCombinedSessionState,
            )

            return CGEventSourceSecondsSinceLastEventType(
                kCGEventSourceStateCombinedSessionState, kCGAnyInputEventType
            )
        except ImportError:
            return 0.0
        except Exception:
            return 0.0
