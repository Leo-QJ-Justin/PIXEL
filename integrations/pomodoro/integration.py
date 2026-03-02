"""Pomodoro timer integration with state machine, countdown, and stats tracking."""

import json
import logging
from datetime import date
from enum import Enum, auto
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer, pyqtSignal

from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)


class PomodoroState(Enum):
    IDLE = auto()
    FOCUS = auto()
    SESSION_COMPLETE = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()


class PomodoroIntegration(BaseIntegration):
    """Focus timer with work/break cycles, session tracking, and stats."""

    timer_tick = pyqtSignal(int)  # remaining_seconds
    state_changed = pyqtSignal(str, dict)  # (state_name, context)
    session_completed = pyqtSignal(int)  # completed_in_cycle
    stats_updated = pyqtSignal(dict)  # full stats dict

    def __init__(self, integration_path: Path, settings: dict[str, Any]):
        super().__init__(integration_path, settings)
        self._state = PomodoroState.IDLE
        self._tick_timer: QTimer | None = None
        self._remaining_seconds = 0
        self._paused = False
        self._completed_in_cycle = 0
        self._stats = self._load_stats()

    @property
    def name(self) -> str:
        return "pomodoro"

    @property
    def display_name(self) -> str:
        return "Pomodoro Timer"

    @property
    def state(self) -> PomodoroState:
        return self._state

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "work_duration_minutes": 25,
            "short_break_minutes": 5,
            "long_break_minutes": 15,
            "auto_start": False,
            "sound_enabled": True,
            "sessions_per_cycle": 4,
        }

    async def start(self) -> None:
        """Load stats and prepare the tick timer."""
        self._stats = self._load_stats()
        self._tick_timer = QTimer()
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._on_tick)
        logger.info("Pomodoro integration started")

    async def stop(self) -> None:
        """Stop timer and save stats."""
        if self._tick_timer is not None:
            self._tick_timer.stop()
            self._tick_timer = None
        self._save_stats()
        logger.info("Pomodoro integration stopped")

    # -- Public control methods --

    def _ensure_timer(self) -> None:
        """Lazily create the tick timer if it doesn't exist yet."""
        if self._tick_timer is None:
            self._tick_timer = QTimer()
            self._tick_timer.setInterval(1000)
            self._tick_timer.timeout.connect(self._on_tick)
            self._stats = self._load_stats()

    def start_session(self) -> None:
        """Start a focus session (IDLE -> FOCUS)."""
        if self._state not in (
            PomodoroState.IDLE,
            PomodoroState.SHORT_BREAK,
            PomodoroState.LONG_BREAK,
        ):
            return
        self._ensure_timer()
        minutes = self._settings.get("work_duration_minutes", 25)
        self._remaining_seconds = minutes * 60
        self._paused = False
        self._transition(PomodoroState.FOCUS)

    def pause(self) -> None:
        """Toggle pause/resume during FOCUS or BREAK states."""
        if self._state not in (
            PomodoroState.FOCUS,
            PomodoroState.SHORT_BREAK,
            PomodoroState.LONG_BREAK,
        ):
            return
        self._paused = not self._paused
        if self._paused:
            self._tick_timer.stop()
        else:
            self._tick_timer.start()

    def skip(self) -> None:
        """Skip the current phase."""
        if self._state == PomodoroState.FOCUS:
            self._record_session()
            self._transition(PomodoroState.SESSION_COMPLETE)
        elif self._state in (PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK):
            self._finish_break()

    def start_break(self) -> None:
        """Start a break after session completion."""
        if self._state != PomodoroState.SESSION_COMPLETE:
            return
        sessions_per_cycle = self._settings.get("sessions_per_cycle", 4)
        if self._completed_in_cycle >= sessions_per_cycle:
            minutes = self._settings.get("long_break_minutes", 15)
            new_state = PomodoroState.LONG_BREAK
        else:
            minutes = self._settings.get("short_break_minutes", 5)
            new_state = PomodoroState.SHORT_BREAK
        self._remaining_seconds = minutes * 60
        self._paused = False
        self._transition(new_state)

    def skip_break(self) -> None:
        """Skip the break from SESSION_COMPLETE and return to IDLE."""
        if self._state != PomodoroState.SESSION_COMPLETE:
            return
        self._transition(PomodoroState.IDLE)

    # -- Timer tick --

    def _on_tick(self) -> None:
        """Decrement countdown, emit tick, handle expiry."""
        if self._paused:
            return
        self._remaining_seconds -= 1
        self.timer_tick.emit(self._remaining_seconds)

        if self._remaining_seconds <= 0:
            self._tick_timer.stop()
            if self._state == PomodoroState.FOCUS:
                self._record_session()
                self._transition(PomodoroState.SESSION_COMPLETE)
            elif self._state in (PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK):
                self._finish_break()

    def _finish_break(self) -> None:
        """Handle break completion."""
        if self._state == PomodoroState.LONG_BREAK:
            self._completed_in_cycle = 0
        auto_start = self._settings.get("auto_start", False)
        if auto_start:
            minutes = self._settings.get("work_duration_minutes", 25)
            self._remaining_seconds = minutes * 60
            self._paused = False
            self._transition(PomodoroState.FOCUS)
        else:
            self._transition(PomodoroState.IDLE)

    # -- State transitions --

    def _transition(self, new_state: PomodoroState) -> None:
        """Handle state transition, emit signals, trigger behaviors."""
        old_state = self._state
        self._state = new_state

        context = {
            "previous_state": old_state.name,
            "remaining_seconds": self._remaining_seconds,
            "completed_in_cycle": self._completed_in_cycle,
        }
        self.state_changed.emit(new_state.name, context)

        if new_state == PomodoroState.FOCUS:
            self._tick_timer.start()
            self.trigger("focus", {"bubble_text": "Focus session started!"})
        elif new_state == PomodoroState.SESSION_COMPLETE:
            self.notify({"bubble_text": "Session complete! Great work!"})
            self.session_completed.emit(self._completed_in_cycle)
        elif new_state in (PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK):
            self._tick_timer.start()
            label = "long break" if new_state == PomodoroState.LONG_BREAK else "short break"
            self.notify({"bubble_text": f"Time for a {label}!"})
        elif new_state == PomodoroState.IDLE:
            if old_state in (PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK):
                self.notify({"bubble_text": "Break over! Ready for more?"})

        self.stats_updated.emit(self._stats)

    # -- Stats persistence --

    def _record_session(self) -> None:
        """Record a completed focus session."""
        self._completed_in_cycle += 1
        self._stats["total_sessions"] = self._stats.get("total_sessions", 0) + 1

        today = date.today().isoformat()
        daily = self._stats.setdefault("daily", {})
        daily[today] = daily.get(today, 0) + 1

        self._update_streak()
        self._save_stats()

    def _update_streak(self) -> None:
        """Update current and longest streak based on daily history."""
        daily = self._stats.get("daily", {})
        if not daily:
            self._stats["current_streak_days"] = 0
            return

        today = date.today()
        streak = 0
        check_date = today
        while check_date.isoformat() in daily:
            streak += 1
            check_date = date.fromordinal(check_date.toordinal() - 1)

        self._stats["current_streak_days"] = streak
        longest = self._stats.get("longest_streak_days", 0)
        if streak > longest:
            self._stats["longest_streak_days"] = streak

    def _load_stats(self) -> dict:
        """Load stats from JSON file, or return defaults."""
        stats_file = self._path / "stats.json"
        if stats_file.exists():
            try:
                with open(stats_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to load pomodoro stats, using defaults")
        return {
            "total_sessions": 0,
            "daily": {},
            "current_streak_days": 0,
            "longest_streak_days": 0,
        }

    def _save_stats(self) -> None:
        """Persist stats to JSON file."""
        stats_file = self._path / "stats.json"
        try:
            self._path.mkdir(parents=True, exist_ok=True)
            with open(stats_file, "w") as f:
                json.dump(self._stats, f, indent=2)
        except OSError:
            logger.exception("Failed to save pomodoro stats")
