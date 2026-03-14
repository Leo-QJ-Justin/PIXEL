"""Wire journal-related events between the React UI and the Python backend."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from integrations.journal.integration import JournalIntegration
    from src.ui.bridge import BridgeHost

logger = logging.getLogger(__name__)


def wire_journal_events(bridge: BridgeHost, integration: JournalIntegration) -> None:
    """Connect all journal bridge events between JS and Python.

    Registers handlers on *bridge* for each ``journal.*`` event that the
    React UI can emit, and uses ``bridge.emit`` to push responses back.
    """

    def _get_store():
        return integration._get_store()

    # ------------------------------------------------------------------
    # journal.loadEntries — last 12 months
    # ------------------------------------------------------------------

    def _on_load_entries(_data: Any) -> None:
        try:
            store = _get_store()
            today = date.today()
            all_entries: list[dict] = []
            for i in range(12):
                d = today - timedelta(days=30 * i)
                entries = store.get_entries_for_month(d.year, d.month)
                all_entries.extend(entries)
            # Deduplicate by date (overlapping month boundaries)
            seen: set[str] = set()
            unique: list[dict] = []
            for entry in all_entries:
                if entry["date"] not in seen:
                    seen.add(entry["date"])
                    unique.append(entry)
            unique.sort(key=lambda e: e["date"])
            bridge.emit("journal.entries", unique)
        except Exception:
            logger.exception("Error loading journal entries")
            bridge.emit("journal.entries", [])

    bridge.on("journal.loadEntries", _on_load_entries)

    # ------------------------------------------------------------------
    # journal.loadEntry — single entry by date
    # ------------------------------------------------------------------

    def _on_load_entry(data: Any) -> None:
        try:
            date_str = data.get("date", "")
            store = _get_store()
            entry = store.get_entry(date_str)
            bridge.emit("journal.entry", entry)
        except Exception:
            logger.exception("Error loading journal entry")
            bridge.emit("journal.entry", None)

    bridge.on("journal.loadEntry", _on_load_entry)

    # ------------------------------------------------------------------
    # journal.save — save full entry
    # ------------------------------------------------------------------

    def _on_save(data: Any) -> None:
        try:
            store = _get_store()
            entry_id = store.save_entry(
                entry_date=data["date"],
                mode=data["mode"],
                mood=data.get("mood"),
                raw_text=data["raw_text"],
                clean_text=data.get("clean_text"),
                prompt_used=data.get("prompt_used"),
            )
            bridge.emit("journal.saved", {"id": entry_id, "date": data["date"]})
            integration.on_entry_saved(data.get("mood"))
        except Exception:
            logger.exception("Error saving journal entry")
            bridge.emit("journal.saved", {"error": True})

    bridge.on("journal.save", _on_save)

    # ------------------------------------------------------------------
    # journal.delete — delete entry by date
    # ------------------------------------------------------------------

    def _on_delete(data: Any) -> None:
        try:
            date_str = data.get("date", "")
            store = _get_store()
            store.delete_entry(date_str)
            bridge.emit("journal.deleted", {"date": date_str})
        except Exception:
            logger.exception("Error deleting journal entry")
            bridge.emit("journal.deleted", {"error": True})

    bridge.on("journal.delete", _on_delete)

    # ------------------------------------------------------------------
    # journal.loadMonth — entries for a year/month
    # ------------------------------------------------------------------

    def _on_load_month(data: Any) -> None:
        try:
            year = data["year"]
            month = data["month"]
            store = _get_store()
            entries = store.get_entries_for_month(year, month)
            dates = [e["date"] for e in entries]
            moods = {e["date"]: e["mood"] for e in entries if e.get("mood")}
            bridge.emit("journal.monthData", {"dates": dates, "moods": moods})
        except Exception:
            logger.exception("Error loading month data")
            bridge.emit("journal.monthData", {"dates": [], "moods": {}})

    bridge.on("journal.loadMonth", _on_load_month)

    # ------------------------------------------------------------------
    # journal.loadStats — streak, total, mood trend, daily prompt
    # ------------------------------------------------------------------

    def _on_load_stats(_data: Any) -> None:
        try:
            store = _get_store()
            current_streak, best_streak = store.get_streak()
            total = store.get_total_count()
            mood_trend = store.get_mood_trend(30)
            bridge.emit(
                "journal.stats",
                {
                    "currentStreak": current_streak,
                    "bestStreak": best_streak,
                    "totalCount": total,
                    "moodTrend": mood_trend,
                },
            )
            prompt = integration.get_daily_prompt()
            bridge.emit("journal.dailyPrompt", {"prompt": prompt})
        except Exception:
            logger.exception("Error loading journal stats")
            bridge.emit("journal.stats", {})

    bridge.on("journal.loadStats", _on_load_stats)

    # ------------------------------------------------------------------
    # journal.cleanup — async LLM cleanup of text
    # ------------------------------------------------------------------

    def _on_cleanup(data: Any) -> None:
        try:
            raw_text = data.get("text", "")
            loop = asyncio.get_running_loop()
            loop.create_task(_async_cleanup(raw_text))
        except Exception:
            logger.exception("Error starting journal cleanup task")
            bridge.emit("journal.cleanupResult", {"error": True})

    async def _async_cleanup(raw_text: str) -> None:
        try:
            from litellm import acompletion

            from config import load_settings

            settings = load_settings()
            pe_settings = settings.get("personality_engine", {})
            model = pe_settings.get("model", "gpt-4o-mini")
            api_key = pe_settings.get("api_key", "")

            response = await acompletion(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a writing assistant. Clean up the following journal "
                            "entry text: fix grammar, spelling, and punctuation while "
                            "preserving the original voice and meaning. Return only the "
                            "cleaned text."
                        ),
                    },
                    {"role": "user", "content": raw_text},
                ],
                api_key=api_key,
            )
            clean = response.choices[0].message.content
            bridge.emit("journal.cleanupResult", {"cleanText": clean})
        except Exception:
            logger.exception("Error during async journal cleanup")
            bridge.emit("journal.cleanupResult", {"error": True})

    bridge.on("journal.cleanup", _on_cleanup)

    logger.info("Journal bridge events wired")
