"""Habits integration — recurring habit tracking with pet accountability."""

from __future__ import annotations

import logging
from datetime import datetime, time
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer

from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)

MILESTONES = [7, 14, 30, 60, 100]


class HabitsIntegration(BaseIntegration):
    """Habit tracker with streaks, reminders, and milestone celebrations."""

    @property
    def name(self) -> str:
        return "habits"

    @property
    def display_name(self) -> str:
        return "Habits"

    def __init__(self, integration_path: Path, settings: dict[str, Any]) -> None:
        super().__init__(integration_path, settings)
        self._reminder_timers: list[QTimer] = []
        self._store = None

    def _get_store(self):
        if self._store is None:
            from integrations.habits.store import HabitStore

            self._store = HabitStore(self._path / "habits.db")
        return self._store

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "daily_summary": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
        }

    async def start(self) -> None:
        self._schedule_reminders()
        logger.info("Habits integration started")

    async def stop(self) -> None:
        for timer in self._reminder_timers:
            timer.stop()
        self._reminder_timers.clear()
        if self._store:
            self._store.close()
            self._store = None
        logger.info("Habits integration stopped")

    def _is_quiet_hours(self) -> bool:
        try:
            start_str = self._settings.get("quiet_hours_start", "22:00")
            end_str = self._settings.get("quiet_hours_end", "07:00")
            h1, m1 = map(int, start_str.split(":"))
            h2, m2 = map(int, end_str.split(":"))
            start = time(h1, m1)
            end = time(h2, m2)
            now = datetime.now().time()
            if start <= end:
                return start <= now <= end
            else:  # Overnight range (e.g., 22:00 - 07:00)
                return now >= start or now <= end
        except (ValueError, AttributeError):
            return False

    def _schedule_reminders(self) -> None:
        """Check reminders every minute."""
        timer = QTimer()
        timer.timeout.connect(self._on_reminder_check)
        timer.start(60 * 1000)  # Every minute
        self._reminder_timers.append(timer)

    def _on_reminder_check(self) -> None:
        if self._is_quiet_hours():
            return
        try:
            store = self._get_store()
            habits = store.list_habits()
            now_str = datetime.now().strftime("%H:%M")
            for habit in habits:
                rt = habit.get("reminder_time")
                if rt and rt == now_str:
                    if not store.is_completed_today(habit["id"]):
                        streak = store.get_streak(habit["id"])
                        msg = f"{habit['icon']} Time to {habit['title']}!"
                        if streak > 0:
                            msg += f" 🔥 {streak} day streak"
                        self.notify({"bubble_text": msg, "bubble_duration_ms": 5000})
        except Exception:
            logger.exception("Error during habit reminder check")

    def on_habit_completed(self, habit_id: str) -> int | None:
        """Called after a habit completion. Returns milestone if hit, else None."""
        try:
            store = self._get_store()
            streak = store.get_streak(habit_id)
            habit = store.get_habit(habit_id)
            if not habit:
                return None

            # Check milestones
            for m in MILESTONES:
                if streak == m:
                    self.trigger(
                        "wave",
                        {
                            "bubble_text": f"🎉 {streak} day streak on {habit['title']}! Amazing!",
                            "bubble_duration_ms": 5000,
                        },
                    )
                    return m
            if streak > 100 and streak % 100 == 0:
                self.trigger(
                    "wave",
                    {
                        "bubble_text": f"🎉 {streak} day streak on {habit['title']}! Incredible!",
                        "bubble_duration_ms": 5000,
                    },
                )
                return streak
            return None
        except Exception:
            logger.exception("Error checking habit milestone")
            return None

    def build_dashboard(self):
        return None
