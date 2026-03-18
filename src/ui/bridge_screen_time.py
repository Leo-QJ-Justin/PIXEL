"""Wire screen time events between the React UI and the Python backend."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from integrations.screen_time.integration import ScreenTimeIntegration
    from src.ui.bridge import BridgeHost

logger = logging.getLogger(__name__)


def wire_screen_time_events(bridge: BridgeHost, integration: ScreenTimeIntegration) -> None:
    """Connect all screen time bridge events between JS and Python."""

    def _get_store():
        return integration._get_store()

    # screentime.today
    def _on_today(data: Any) -> None:
        try:
            store = _get_store()
            day = data.get("date") if data else None
            if not day:
                day = date.today().isoformat()
            yesterday = (date.fromisoformat(day) - timedelta(days=1)).isoformat()

            total = store.get_daily_total(day)
            comparison = total - store.get_daily_total(yesterday)
            breakdown = store.get_category_breakdown(day)
            top_apps = store.get_top_apps(day)
            timeline = store.get_timeline(day)

            bridge.emit("screentime.todayResult", {
                "total_s": total,
                "comparison_s": comparison,
                "category_breakdown": breakdown,
                "top_apps": top_apps,
                "timeline": timeline,
            })
        except Exception:
            logger.exception("Error loading today screen time")
            bridge.emit("screentime.error", {"message": "Failed to load screen time data"})

    bridge.on("screentime.today", _on_today)

    # screentime.week
    def _on_week(data: Any) -> None:
        try:
            store = _get_store()
            ws = data.get("week_start") if data else None
            if not ws:
                today = date.today()
                ws = (today - timedelta(days=today.weekday())).isoformat()

            daily_totals = store.get_weekly_totals(ws)
            total = sum(d["total_s"] for d in daily_totals)
            avg = total // 7 if daily_totals else 0

            # Previous week for trend
            prev_ws = (date.fromisoformat(ws) - timedelta(weeks=1)).isoformat()
            prev_totals = store.get_weekly_totals(prev_ws)
            prev_total = sum(d["total_s"] for d in prev_totals)
            trend = total - prev_total

            week_end = (date.fromisoformat(ws) + timedelta(days=7)).isoformat()
            top_apps = store.get_top_apps_range(ws, week_end, limit=10)

            bridge.emit("screentime.weekResult", {
                "daily_totals": daily_totals,
                "avg_s": avg,
                "total_s": total,
                "trend_s": trend,
                "top_apps": top_apps,
            })
        except Exception:
            logger.exception("Error loading week screen time")
            bridge.emit("screentime.error", {"message": "Failed to load weekly data"})

    bridge.on("screentime.week", _on_week)

    # screentime.categories
    def _on_categories(_data: Any) -> None:
        try:
            store = _get_store()
            categories = store.get_all_categories()
            bridge.emit("screentime.categoriesResult", {"categories": categories})
        except Exception:
            logger.exception("Error loading categories")
            bridge.emit("screentime.error", {"message": "Failed to load categories"})

    bridge.on("screentime.categories", _on_categories)

    # screentime.updateCategory
    def _on_update_category(data: Any) -> None:
        try:
            store = _get_store()
            store.update_category(
                data["exe_name"],
                data["category"],
                data.get("display_name"),
            )
            row = {"exe_name": data["exe_name"], "category": data["category"], "display_name": data.get("display_name")}
            bridge.emit("screentime.categoryUpdated", {"category": row})
        except Exception:
            logger.exception("Error updating category")
            bridge.emit("screentime.error", {"message": "Failed to update category"})

    bridge.on("screentime.updateCategory", _on_update_category)

    # screentime.clear
    def _on_clear(_data: Any) -> None:
        try:
            store = _get_store()
            store.clear_all()
            bridge.emit("screentime.cleared", {})
        except Exception:
            logger.exception("Error clearing screen time data")
            bridge.emit("screentime.error", {"message": "Failed to clear data"})

    bridge.on("screentime.clear", _on_clear)

    logger.info("Screen Time bridge events wired")
