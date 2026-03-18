"""Workspaces integration — grouped app/URL/folder launcher."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)


class WorkspacesIntegration(BaseIntegration):
    """Launch groups of apps, URLs, and folders with one click."""

    @property
    def name(self) -> str:
        return "workspaces"

    @property
    def display_name(self) -> str:
        return "Workspaces"

    def __init__(self, integration_path: Path, settings: dict[str, Any]) -> None:
        super().__init__(integration_path, settings)
        self._data_path = integration_path / "workspaces.json"
        self._workspaces: list[dict] = []

    def get_default_settings(self) -> dict[str, Any]:
        return {"enabled": True}

    async def start(self) -> None:
        self._load()
        logger.info("Workspaces integration started (%d workspaces)", len(self._workspaces))

    async def stop(self) -> None:
        logger.info("Workspaces integration stopped")

    def _load(self) -> None:
        if self._data_path.exists():
            try:
                with open(self._data_path) as f:
                    data = json.load(f)
                self._workspaces = data.get("workspaces", [])
            except (json.JSONDecodeError, KeyError):
                logger.exception("Error loading workspaces.json")
                self._workspaces = []
        else:
            self._workspaces = []

    def _save(self) -> None:
        self._data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._data_path, "w") as f:
            json.dump({"workspaces": self._workspaces}, f, indent=2)

    def list_workspaces(self) -> list[dict]:
        return self._workspaces

    def create_workspace(
        self,
        name: str,
        icon: str = "🚀",
        description: str | None = None,
        color: str | None = None,
        behavior: str | None = None,
    ) -> dict:
        ws = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description or "",
            "icon": icon,
            "color": color or "#3B7DD8",
            "behavior": behavior,
            "sort_order": len(self._workspaces),
            "last_launched": None,
            "items": [],
        }
        self._workspaces.append(ws)
        self._save()
        return ws

    def update_workspace(self, ws_id: str, **fields) -> dict | None:
        ws = self._find(ws_id)
        if not ws:
            return None
        allowed = {"name", "description", "icon", "color", "behavior", "sort_order"}
        for k, v in fields.items():
            if k in allowed:
                ws[k] = v
        self._save()
        return ws

    def delete_workspace(self, ws_id: str) -> None:
        self._workspaces = [w for w in self._workspaces if w["id"] != ws_id]
        self._save()

    def add_item(self, ws_id: str, item_type: str, path: str, display_name: str) -> dict | None:
        ws = self._find(ws_id)
        if not ws:
            return None
        item = {
            "id": str(uuid.uuid4()),
            "type": item_type,
            "path": path,
            "display_name": display_name,
        }
        ws["items"].append(item)
        self._save()
        return ws

    def remove_item(self, ws_id: str, item_id: str) -> dict | None:
        ws = self._find(ws_id)
        if not ws:
            return None
        ws["items"] = [i for i in ws["items"] if i["id"] != item_id]
        self._save()
        return ws

    def launch_workspace(self, ws_id: str) -> tuple[bool, list[str]]:
        """Launch all items in a workspace. Returns (success, errors)."""
        from integrations.workspaces.launcher import Launcher, LaunchError

        ws = self._find(ws_id)
        if not ws:
            return False, ["Workspace not found"]

        launcher = Launcher()
        errors: list[str] = []

        for item in ws.get("items", []):
            try:
                launcher.launch_item(item["type"], item["path"])
            except LaunchError as e:
                errors.append(str(e))

        # Update last_launched
        ws["last_launched"] = datetime.now().isoformat()
        self._save()

        # Trigger pet behavior if configured
        behavior = ws.get("behavior")
        if behavior:
            self.trigger(behavior, {
                "bubble_text": f"{ws['icon']} {ws['name']} workspace launched!",
                "bubble_duration_ms": 3000,
            })
        else:
            self.notify({
                "bubble_text": f"{ws['icon']} {ws['name']} workspace launched!",
                "bubble_duration_ms": 3000,
            })

        return len(errors) == 0, errors

    def _find(self, ws_id: str) -> dict | None:
        return next((w for w in self._workspaces if w["id"] == ws_id), None)

    def build_dashboard(self):
        return None
