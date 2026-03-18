"""Wire habit-related events between the React UI and the Python backend."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from integrations.habits.integration import HabitsIntegration
    from src.ui.bridge import BridgeHost

logger = logging.getLogger(__name__)


def wire_habits_events(bridge: BridgeHost, integration: HabitsIntegration) -> None:
    """Connect all habits bridge events between JS and Python."""

    def _get_store():
        return integration._get_store()

    # habits.today
    def _on_today(_data: Any) -> None:
        try:
            store = _get_store()
            habits = store.get_today_status()
            bridge.emit("habits.todayResult", {"habits": habits})
        except Exception:
            logger.exception("Error loading today habits")
            bridge.emit("habits.error", {"message": "Failed to load habits"})

    bridge.on("habits.today", _on_today)

    # habits.list
    def _on_list(data: Any) -> None:
        try:
            include_archived = data.get("include_archived", False) if data else False
            store = _get_store()
            habits = store.list_habits(include_archived=include_archived)
            bridge.emit("habits.listResult", {"habits": habits})
        except Exception:
            logger.exception("Error listing habits")
            bridge.emit("habits.error", {"message": "Failed to list habits"})

    bridge.on("habits.list", _on_list)

    # habits.complete
    def _on_complete(data: Any) -> None:
        try:
            store = _get_store()
            store.complete_today(data["id"])
            milestone = integration.on_habit_completed(data["id"])
            status = store.get_today_status()
            habit_status = next((h for h in status if h["id"] == data["id"]), None)
            result: dict = {"habit": habit_status}
            if milestone:
                result["milestone"] = milestone
            bridge.emit("habits.completed", result)
        except Exception:
            logger.exception("Error completing habit")
            bridge.emit("habits.error", {"message": "Failed to complete habit"})

    bridge.on("habits.complete", _on_complete)

    # habits.uncomplete
    def _on_uncomplete(data: Any) -> None:
        try:
            store = _get_store()
            store.uncomplete_today(data["id"])
            status = store.get_today_status()
            habit_status = next((h for h in status if h["id"] == data["id"]), None)
            bridge.emit("habits.uncompleted", {"habit": habit_status})
        except Exception:
            logger.exception("Error uncompleting habit")
            bridge.emit("habits.error", {"message": "Failed to uncomplete habit"})

    bridge.on("habits.uncomplete", _on_uncomplete)

    # habits.create
    def _on_create(data: Any) -> None:
        try:
            store = _get_store()
            habit = store.create_habit(
                title=data["title"],
                icon=data.get("icon", "✅"),
                frequency=data.get("frequency", "daily"),
                target_count=data.get("target_count", 1),
                reminder_time=data.get("reminder_time"),
            )
            bridge.emit("habits.created", {"habit": habit})
        except Exception:
            logger.exception("Error creating habit")
            bridge.emit("habits.error", {"message": "Failed to create habit"})

    bridge.on("habits.create", _on_create)

    # habits.update
    def _on_update(data: Any) -> None:
        try:
            habit_id = data["id"]
            fields = {k: v for k, v in data.items() if k != "id"}
            store = _get_store()
            habit = store.update_habit(habit_id, **fields)
            bridge.emit("habits.updated", {"habit": habit})
        except Exception:
            logger.exception("Error updating habit")
            bridge.emit("habits.error", {"message": "Failed to update habit"})

    bridge.on("habits.update", _on_update)

    # habits.delete
    def _on_delete(data: Any) -> None:
        try:
            store = _get_store()
            store.delete_habit(data["id"])
            bridge.emit("habits.deleted", {"id": data["id"]})
        except Exception:
            logger.exception("Error deleting habit")
            bridge.emit("habits.error", {"message": "Failed to delete habit"})

    bridge.on("habits.delete", _on_delete)

    # habits.stats
    def _on_stats(data: Any) -> None:
        try:
            store = _get_store()
            habit_id = data["id"]
            bridge.emit(
                "habits.statsResult",
                {
                    "id": habit_id,
                    "streak": store.get_streak(habit_id),
                    "longest_streak": store.get_longest_streak(habit_id),
                    "completion_rate": store.get_completion_rate(habit_id),
                    "total": store.get_total_completions(habit_id),
                },
            )
        except Exception:
            logger.exception("Error loading habit stats")
            bridge.emit("habits.error", {"message": "Failed to load stats"})

    bridge.on("habits.stats", _on_stats)

    # habits.week
    def _on_week(data: Any) -> None:
        try:
            store = _get_store()
            week_start = data["week_start"]
            habits = store.list_habits()
            completions = {}
            for h in habits:
                completions[h["id"]] = store.get_week_completions(h["id"], week_start)
            bridge.emit("habits.weekResult", {"completions": completions})
        except Exception:
            logger.exception("Error loading week data")
            bridge.emit("habits.error", {"message": "Failed to load week data"})

    bridge.on("habits.week", _on_week)

    logger.info("Habits bridge events wired")
