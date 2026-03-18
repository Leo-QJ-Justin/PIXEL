"""Wire dashboard home events — aggregates summary data from all integrations."""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.integration_manager import IntegrationManager
    from src.ui.bridge import BridgeHost

logger = logging.getLogger(__name__)


def wire_dashboard_events(bridge: BridgeHost, integration_manager: IntegrationManager) -> None:
    """Connect dashboard summary events."""

    def _on_load_summary(_data: Any) -> None:
        summary: dict[str, Any] = {
            "greeting": _get_greeting(),
            "weather": None,
            "calendar_next": None,
            "tasks": None,
            "habits": None,
            "pomodoro": None,
            "screen_time": None,
            "journal": None,
        }

        # Tasks summary
        tasks_int = integration_manager.get_integration("tasks")
        if tasks_int and tasks_int.enabled:
            try:
                store = tasks_int._get_store()
                today_tasks = store.get_today_tasks()
                overdue = store.get_overdue_tasks()
                summary["tasks"] = {
                    "due_today": len(today_tasks),
                    "overdue": len(overdue),
                }
            except Exception:
                logger.debug("Error getting tasks summary", exc_info=True)

        # Habits summary
        habits_int = integration_manager.get_integration("habits")
        if habits_int and habits_int.enabled:
            try:
                store = habits_int._get_store()
                status = store.get_today_status()
                done = sum(1 for h in status if h["completed_today"])
                total = len(status)
                best_streak = max((h["streak"] for h in status), default=0)
                summary["habits"] = {
                    "done": done,
                    "total": total,
                    "streak": best_streak,
                }
            except Exception:
                logger.debug("Error getting habits summary", exc_info=True)

        # Pomodoro summary
        pomo_int = integration_manager.get_integration("pomodoro")
        if pomo_int and pomo_int.enabled:
            try:
                today_str = date.today().isoformat()
                stats = pomo_int.get_stats()
                daily = stats.get("daily", {})
                today_count = daily.get(today_str, 0)
                summary["pomodoro"] = {
                    "sessions_today": today_count,
                    "minutes_today": today_count * 25,
                    "streak": stats.get("streak", 0),
                }
            except Exception:
                logger.debug("Error getting pomodoro summary", exc_info=True)

        # Screen time summary
        st_int = integration_manager.get_integration("screen_time")
        if st_int and st_int.enabled:
            try:
                store = st_int._get_store()
                today_str = date.today().isoformat()
                total_s = store.get_daily_total(today_str)
                breakdown = store.get_category_breakdown(today_str)
                productive = breakdown.get("Productive", 0)
                pct = round(productive / total_s * 100) if total_s > 0 else 0
                summary["screen_time"] = {
                    "total_s": total_s,
                    "productive_pct": pct,
                    "breakdown": breakdown,
                }
            except Exception:
                logger.debug("Error getting screen time summary", exc_info=True)

        # Journal summary
        journal_int = integration_manager.get_integration("journal")
        if journal_int and journal_int.enabled:
            try:
                store = journal_int._get_store()
                today_entry = store.get_entry(date.today().isoformat())
                current_streak, _ = store.get_streak()
                prompt = journal_int.get_daily_prompt()
                summary["journal"] = {
                    "written_today": today_entry is not None,
                    "streak": current_streak,
                    "prompt": prompt,
                }
            except Exception:
                logger.debug("Error getting journal summary", exc_info=True)

        # Weather
        weather_int = integration_manager.get_integration("weather")
        if weather_int and weather_int.enabled:
            try:
                data = weather_int.get_current()
                if data:
                    summary["weather"] = {
                        "temp": data.get("temp"),
                        "condition": data.get("condition"),
                        "city": data.get("city"),
                    }
            except Exception:
                logger.debug("Error getting weather", exc_info=True)

        # Calendar next event
        cal_int = integration_manager.get_integration("google_calendar")
        if cal_int and cal_int.enabled:
            try:
                event = cal_int.get_next_event()
                if event:
                    summary["calendar_next"] = {
                        "summary": event.summary,
                        "start_time": event.start_time.strftime("%H:%M"),
                        "minutes_until": int(
                            (
                                event.start_time - __import__("datetime").datetime.now()
                            ).total_seconds()
                            / 60
                        ),
                    }
            except Exception:
                logger.debug("Error getting calendar", exc_info=True)

        bridge.emit("dashboard.summaryResult", summary)

    bridge.on("dashboard.loadSummary", _on_load_summary)
    logger.info("Dashboard bridge events wired")


def _get_greeting() -> str:
    from datetime import datetime

    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"
