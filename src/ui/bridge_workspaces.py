"""Wire workspace events between the React UI and the Python backend."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import QFileDialog

if TYPE_CHECKING:
    from integrations.workspaces.integration import WorkspacesIntegration
    from src.ui.bridge import BridgeHost

logger = logging.getLogger(__name__)


def wire_workspaces_events(bridge: BridgeHost, integration: WorkspacesIntegration) -> None:
    """Connect all workspaces bridge events between JS and Python."""

    # workspaces.list
    def _on_list(_data: Any) -> None:
        try:
            workspaces = integration.list_workspaces()
            bridge.emit("workspaces.listResult", {"workspaces": workspaces})
        except Exception:
            logger.exception("Error listing workspaces")
            bridge.emit("workspaces.error", {"message": "Failed to load workspaces"})

    bridge.on("workspaces.list", _on_list)

    # workspaces.create
    def _on_create(data: Any) -> None:
        try:
            ws = integration.create_workspace(
                name=data["name"],
                icon=data.get("icon", "🚀"),
                description=data.get("description"),
                color=data.get("color"),
                behavior=data.get("behavior"),
            )
            bridge.emit("workspaces.created", {"workspace": ws})
        except Exception:
            logger.exception("Error creating workspace")
            bridge.emit("workspaces.error", {"message": "Failed to create workspace"})

    bridge.on("workspaces.create", _on_create)

    # workspaces.update
    def _on_update(data: Any) -> None:
        try:
            ws_id = data.pop("id")
            ws = integration.update_workspace(ws_id, **data)
            bridge.emit("workspaces.updated", {"workspace": ws})
        except Exception:
            logger.exception("Error updating workspace")
            bridge.emit("workspaces.error", {"message": "Failed to update workspace"})

    bridge.on("workspaces.update", _on_update)

    # workspaces.delete
    def _on_delete(data: Any) -> None:
        try:
            integration.delete_workspace(data["id"])
            bridge.emit("workspaces.deleted", {"id": data["id"]})
        except Exception:
            logger.exception("Error deleting workspace")
            bridge.emit("workspaces.error", {"message": "Failed to delete workspace"})

    bridge.on("workspaces.delete", _on_delete)

    # workspaces.addItem
    def _on_add_item(data: Any) -> None:
        try:
            ws = integration.add_item(
                data["workspace_id"], data["type"], data["path"], data["display_name"]
            )
            bridge.emit("workspaces.itemAdded", {"workspace": ws})
        except Exception:
            logger.exception("Error adding item")
            bridge.emit("workspaces.error", {"message": "Failed to add item"})

    bridge.on("workspaces.addItem", _on_add_item)

    # workspaces.removeItem
    def _on_remove_item(data: Any) -> None:
        try:
            ws = integration.remove_item(data["workspace_id"], data["item_id"])
            bridge.emit("workspaces.itemRemoved", {"workspace": ws})
        except Exception:
            logger.exception("Error removing item")
            bridge.emit("workspaces.error", {"message": "Failed to remove item"})

    bridge.on("workspaces.removeItem", _on_remove_item)

    # workspaces.launch
    def _on_launch(data: Any) -> None:
        try:
            success, errors = integration.launch_workspace(data["id"])
            bridge.emit("workspaces.launched", {"success": success, "errors": errors})
        except Exception:
            logger.exception("Error launching workspace")
            bridge.emit("workspaces.error", {"message": "Failed to launch workspace"})

    bridge.on("workspaces.launch", _on_launch)

    # workspaces.browseFile
    def _on_browse_file(_data: Any) -> None:
        path, _ = QFileDialog.getOpenFileName(None, "Select Application")
        bridge.emit("workspaces.browseFileResult", {"path": path or None})

    bridge.on("workspaces.browseFile", _on_browse_file)

    # workspaces.browseFolder
    def _on_browse_folder(_data: Any) -> None:
        path = QFileDialog.getExistingDirectory(None, "Select Folder")
        bridge.emit("workspaces.browseFolderResult", {"path": path or None})

    bridge.on("workspaces.browseFolder", _on_browse_folder)

    logger.info("Workspaces bridge events wired")
