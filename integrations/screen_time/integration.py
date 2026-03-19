"""Screen Time integration — track foreground app usage with pet nudging."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer

from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)

IDLE_THRESHOLD_S = 300  # 5 minutes
POLL_INTERVAL_MS = 5000  # 5 seconds
FLUSH_INTERVAL_MS = 60000  # 1 minute

# Process names belonging to PIXEL itself (should not be tracked)
_SELF_EXE_NAMES = frozenset({
    "pythonw.exe", "python.exe", "pythonw", "python",
    "mc-web-view", "mc-web-view.exe",
    "QtWebEngineProcess", "QtWebEngineProcess.exe",
})


class ScreenTimeIntegration(BaseIntegration):
    """Foreground app tracking with break reminders and distraction alerts."""

    @property
    def name(self) -> str:
        return "screen_time"

    @property
    def display_name(self) -> str:
        return "Screen Time"

    def __init__(self, integration_path: Path, settings: dict[str, Any]) -> None:
        super().__init__(integration_path, settings)
        self._poll_timer: QTimer | None = None
        self._flush_timer: QTimer | None = None
        self._break_timer: QTimer | None = None
        self._tracker = None
        self._store = None

        # In-memory current session
        self._current_app: str | None = None
        self._current_exe: str | None = None
        self._current_title: str | None = None
        self._session_start: datetime | None = None

        # Pending sessions to flush
        self._pending_sessions: list[tuple] = []

        # Break reminder state
        self._continuous_active_s: float = 0
        self._break_reminded = False

    @property
    def continuous_active_seconds(self) -> float:
        """How long the user has been continuously active (resets after idle)."""
        return self._continuous_active_s

    def _get_store(self):
        if self._store is None:
            from integrations.screen_time.store import ScreenTimeStore

            self._store = ScreenTimeStore(self._path / "screen_time.db")
        return self._store

    def _get_tracker(self):
        if self._tracker is None:
            from integrations.screen_time.tracker import create_tracker

            self._tracker = create_tracker()
        return self._tracker

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "break_reminder_hours": 2,
            "distraction_alert_minutes": 30,
            "track_window_titles": False,
            "retention_days": 90,
        }

    async def start(self) -> None:
        # Prune old data
        retention = self._settings.get("retention_days", 90)
        try:
            self._get_store().prune_old_data(retention)
        except Exception:
            logger.exception("Error pruning old screen time data")

        # Poll timer
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._on_poll)
        self._poll_timer.start(POLL_INTERVAL_MS)

        # Flush timer
        self._flush_timer = QTimer()
        self._flush_timer.timeout.connect(self._flush_pending)
        self._flush_timer.start(FLUSH_INTERVAL_MS)

        # Break reminder timer (check every minute)
        self._break_timer = QTimer()
        self._break_timer.timeout.connect(self._on_break_check)
        self._break_timer.start(60000)

        logger.info("Screen Time integration started")

    async def stop(self) -> None:
        for timer in [self._poll_timer, self._flush_timer, self._break_timer]:
            if timer:
                timer.stop()
        self._poll_timer = None
        self._flush_timer = None
        self._break_timer = None

        # Finalize current session
        self._finalize_session()
        self._flush_pending()

        if self._store:
            self._store.close()
            self._store = None
        logger.info("Screen Time integration stopped")

    def _on_poll(self) -> None:
        try:
            tracker = self._get_tracker()
            idle_s = tracker.get_idle_seconds()

            if idle_s >= IDLE_THRESHOLD_S:
                self._finalize_session()
                self._continuous_active_s = 0
                self._break_reminded = False
                return

            window = tracker.get_active_window()
            if not window:
                return

            # Skip PIXEL's own processes
            if window.exe_name in _SELF_EXE_NAMES or window.pid == os.getpid():
                return

            now = datetime.now()
            self._continuous_active_s += POLL_INTERVAL_MS / 1000

            if self._current_exe == window.exe_name:
                # Same app — extend session (no action needed, ended_at computed on finalize)
                return

            # Different app — finalize old, start new
            self._finalize_session()
            track_titles = self._settings.get("track_window_titles", False)
            self._current_app = window.app_name
            self._current_exe = window.exe_name
            self._current_title = window.window_title if track_titles else None
            self._session_start = now

        except Exception:
            logger.warning("Error during screen time poll", exc_info=True)

    def _finalize_session(self) -> None:
        if self._current_exe and self._session_start:
            now = datetime.now()
            self._pending_sessions.append(
                (
                    self._current_app,
                    self._current_exe,
                    self._current_title,
                    self._session_start,
                    now,
                )
            )
            self._current_app = None
            self._current_exe = None
            self._current_title = None
            self._session_start = None

    def _flush_pending(self) -> None:
        # Checkpoint the current active session so it appears in queries
        if self._current_exe and self._session_start:
            now = datetime.now()
            self._pending_sessions.append((
                self._current_app,
                self._current_exe,
                self._current_title,
                self._session_start,
                now,
            ))
            self._session_start = now  # restart from this point

        if not self._pending_sessions:
            return
        try:
            store = self._get_store()
        except Exception:
            logger.exception(
                "Cannot access screen time store — %d sessions pending", len(self._pending_sessions)
            )
            if len(self._pending_sessions) > 1000:
                logger.error(
                    "Dropping %d pending sessions to prevent memory growth",
                    len(self._pending_sessions),
                )
                self._pending_sessions.clear()
            return
        failed = []
        for session in self._pending_sessions:
            try:
                store.save_session(*session)
            except Exception:
                logger.exception("Failed to save screen time session")
                failed.append(session)
        self._pending_sessions = failed

    def _on_break_check(self) -> None:
        threshold_hours = self._settings.get("break_reminder_hours", 2)
        threshold_s = threshold_hours * 3600
        if self._continuous_active_s >= threshold_s and not self._break_reminded:
            self._break_reminded = True
            hours = int(self._continuous_active_s // 3600)
            self.notify(
                {
                    "bubble_text": f"You've been at it for {hours}h — time for a break? 🧘",
                    "bubble_duration_ms": 5000,
                }
            )

    def build_dashboard(self):
        return None
