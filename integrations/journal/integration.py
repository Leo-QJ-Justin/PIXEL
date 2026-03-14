"""Journal integration — local journaling with pet companion."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer

from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)


class JournalIntegration(BaseIntegration):
    """Local journal with nudging, prompts, and mood-matched reactions."""

    @property
    def name(self) -> str:
        return "journal"

    @property
    def display_name(self) -> str:
        return "Journal"

    def __init__(self, integration_path: Path, settings: dict[str, Any]) -> None:
        super().__init__(integration_path, settings)
        self._nudge_timer: QTimer | None = None
        self._nudged_today: bool = False
        self._last_nudge_date: str = ""
        self._prompts: list[dict] = []
        self._load_prompts()

        # Lazy imports to avoid circular deps
        self._store = None
        self._dashboard = None

    def _load_prompts(self) -> None:
        prompts_file = Path(__file__).parent / "prompts.json"
        if prompts_file.exists():
            with open(prompts_file) as f:
                data = json.load(f)
            self._prompts = data.get("prompts", [])

    def _get_store(self):
        if self._store is None:
            from integrations.journal.store import JournalStore

            self._store = JournalStore(self._path / "journal.db")
        return self._store

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": False,
            "nudge_frequency": "smart",
            "nudge_time": "20:00",
            "blur_on_focus_loss": True,
        }

    def get_daily_prompt(self, date_str: str | None = None) -> str:
        """Get the prompt for a given date (deterministic by date)."""
        if not self._prompts:
            return "How was your day?"
        d = date_str or date.today().isoformat()
        index = hash(d) % len(self._prompts)
        return self._prompts[index]["text"]

    async def start(self) -> None:
        """Start the journal integration (set up nudge timer)."""
        freq = self._settings.get("nudge_frequency", "smart")
        if freq == "never":
            return

        interval_ms = 30 * 60 * 1000  # 30 minutes for smart mode
        if freq == "once_daily":
            interval_ms = 60 * 1000  # Check every minute for daily mode

        self._nudge_timer = QTimer()
        self._nudge_timer.timeout.connect(self._on_nudge_check)
        self._nudge_timer.start(interval_ms)
        logger.info("Journal nudge timer started")

    async def stop(self) -> None:
        """Stop the journal integration."""
        if self._nudge_timer:
            self._nudge_timer.stop()
            self._nudge_timer = None
        if self._store:
            self._store.close()
            self._store = None
        logger.info("Journal integration stopped")

    def _should_nudge(self) -> bool:
        """Determine whether to nudge the user to journal."""
        freq = self._settings.get("nudge_frequency", "smart")
        if freq == "never":
            return False

        # Reset flag on new day
        today = date.today().isoformat()
        if self._last_nudge_date != today:
            self._nudged_today = False
            self._last_nudge_date = today

        if self._nudged_today:
            return False

        # Check if entry exists for today
        store = self._get_store()
        if store.get_entry(today) is not None:
            return False

        if freq == "once_daily":
            return True

        # Smart mode: check if within 2 hours of nudge time
        nudge_time_str = self._settings.get("nudge_time", "20:00")
        try:
            h, m = map(int, nudge_time_str.split(":"))
            nudge_time = time(h, m)
        except (ValueError, AttributeError):
            nudge_time = time(20, 0)

        now = datetime.now().time()
        nudge_dt = datetime.combine(date.today(), nudge_time)
        now_dt = datetime.combine(date.today(), now)
        diff = abs((now_dt - nudge_dt).total_seconds())
        return diff <= 2 * 3600  # within 2 hours

    def _on_nudge_check(self) -> None:
        """Timer callback to check if we should nudge."""
        if self._should_nudge():
            self._nudged_today = True
            prompt = self.get_daily_prompt()
            self.notify(
                {
                    "bubble_text": f'Want to write about your day?\n\n"{prompt}"',
                    "duration": 8000,
                }
            )

    def on_entry_saved(self, mood: str | None) -> None:
        """Called when a journal entry is saved. Triggers pet reactions."""
        if mood in ("\U0001f60a", "\U0001f604"):
            self.trigger("happy", {"bubble_text": "Glad you're feeling good!"})
        elif mood in ("\U0001f622", "\U0001f61e"):
            self.trigger("comfort", {"bubble_text": "I'm here for you."})
        else:
            self.notify({"bubble_text": "Entry saved!", "duration": 3000})

        # Check for streak milestones
        store = self._get_store()
        current, _ = store.get_streak()
        if current > 0 and current % 7 == 0:
            self.notify(
                {
                    "bubble_text": f"That's {current} days in a row! Keep it up!",
                    "duration": 5000,
                }
            )

    def build_dashboard(self):
        """Dashboard is now provided by the React panel host."""
        return None
