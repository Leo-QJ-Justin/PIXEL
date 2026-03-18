"""Tasks integration — local todo list with pet nudging."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer

from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)


class TasksIntegration(BaseIntegration):
    """Local-first task management with overdue nudges and completion celebrations."""

    @property
    def name(self) -> str:
        return "tasks"

    @property
    def display_name(self) -> str:
        return "Tasks"

    def __init__(self, integration_path: Path, settings: dict[str, Any]) -> None:
        super().__init__(integration_path, settings)
        self._overdue_timer: QTimer | None = None
        self._last_nudge_overdue_ids: set[str] = set()
        self._store = None

    def _get_store(self):
        if self._store is None:
            from integrations.tasks.store import TaskStore

            self._store = TaskStore(self._path / "tasks.db")
        return self._store

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "nudge_frequency_minutes": 120,
            "daily_summary": True,
        }

    async def start(self) -> None:
        nudge_ms = self._settings.get("nudge_frequency_minutes", 120) * 60 * 1000
        self._overdue_timer = QTimer()
        self._overdue_timer.timeout.connect(self._on_overdue_check)
        self._overdue_timer.start(nudge_ms)
        logger.info("Tasks integration started (overdue check every %d min)", nudge_ms // 60000)

    async def stop(self) -> None:
        if self._overdue_timer:
            self._overdue_timer.stop()
            self._overdue_timer = None
        if self._store:
            self._store.close()
            self._store = None
        logger.info("Tasks integration stopped")

    def _on_overdue_check(self) -> None:
        try:
            store = self._get_store()
            overdue = store.get_overdue_tasks()
            if not overdue:
                return
            overdue_ids = {t["id"] for t in overdue}
            if overdue_ids == self._last_nudge_overdue_ids:
                return  # Don't re-nudge for the same set
            self._last_nudge_overdue_ids = overdue_ids
            n = len(overdue)
            self.notify(
                {
                    "bubble_text": f"You have {n} overdue task{'s' if n != 1 else ''} — want to check them off?",
                    "bubble_duration_ms": 5000,
                }
            )
        except Exception:
            logger.exception("Error during overdue check")

    def on_task_completed(self, title: str) -> None:
        self.trigger("wave", {"bubble_text": f"Nice! '{title}' done ✓", "bubble_duration_ms": 3000})

    def get_today_summary(self) -> str | None:
        try:
            store = self._get_store()
            today = store.get_today_tasks()
            if not today:
                return None
            n = len(today)
            return f"You have {n} task{'s' if n != 1 else ''} due today"
        except Exception:
            logger.exception("Error getting task summary")
            return None

    def build_dashboard(self):
        return None
