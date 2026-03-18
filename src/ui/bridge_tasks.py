"""Wire task-related events between the React UI and the Python backend."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from integrations.tasks.integration import TasksIntegration
    from src.ui.bridge import BridgeHost

logger = logging.getLogger(__name__)


def wire_tasks_events(bridge: BridgeHost, integration: TasksIntegration) -> None:
    """Connect all tasks bridge events between JS and Python."""

    def _get_store():
        return integration._get_store()

    # tasks.list
    def _on_list(data: Any) -> None:
        try:
            include_completed = data.get("include_completed", False) if data else False
            store = _get_store()
            tasks = store.list_tasks(include_completed=include_completed)
            bridge.emit("tasks.listResult", {"tasks": tasks})
        except Exception:
            logger.exception("Error listing tasks")
            bridge.emit("tasks.error", {"message": "Failed to load tasks"})

    bridge.on("tasks.list", _on_list)

    # tasks.create
    def _on_create(data: Any) -> None:
        try:
            store = _get_store()
            task = store.create_task(
                title=data["title"],
                due_date=data.get("due_date"),
                tag=data.get("tag"),
                priority=data.get("priority", 0),
                parent_id=data.get("parent_id"),
                notes=data.get("notes"),
            )
            bridge.emit("tasks.created", {"task": task})
        except Exception:
            logger.exception("Error creating task")
            bridge.emit("tasks.error", {"message": "Failed to create task"})

    bridge.on("tasks.create", _on_create)

    # tasks.update
    def _on_update(data: Any) -> None:
        try:
            task_id = data.pop("id")
            store = _get_store()
            task = store.update_task(task_id, **data)
            bridge.emit("tasks.updated", {"task": task})
        except Exception:
            logger.exception("Error updating task")
            bridge.emit("tasks.error", {"message": "Failed to update task"})

    bridge.on("tasks.update", _on_update)

    # tasks.complete
    def _on_complete(data: Any) -> None:
        try:
            store = _get_store()
            task = store.complete_task(data["id"])
            bridge.emit("tasks.completed", {"task": task})
            if task:
                integration.on_task_completed(task["title"])
        except Exception:
            logger.exception("Error completing task")
            bridge.emit("tasks.error", {"message": "Failed to complete task"})

    bridge.on("tasks.complete", _on_complete)

    # tasks.delete
    def _on_delete(data: Any) -> None:
        try:
            store = _get_store()
            store.delete_task(data["id"])
            bridge.emit("tasks.deleted", {"id": data["id"]})
        except Exception:
            logger.exception("Error deleting task")
            bridge.emit("tasks.error", {"message": "Failed to delete task"})

    bridge.on("tasks.delete", _on_delete)

    # tasks.reorder
    def _on_reorder(data: Any) -> None:
        try:
            store = _get_store()
            store.reorder_tasks(data["task_ids"])
            bridge.emit("tasks.reordered", {})
        except Exception:
            logger.exception("Error reordering tasks")
            bridge.emit("tasks.error", {"message": "Failed to reorder tasks"})

    bridge.on("tasks.reorder", _on_reorder)

    logger.info("Tasks bridge events wired")
