"""Wire settings-related events between the React UI and the Python backend."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from config import load_settings, save_settings

if TYPE_CHECKING:
    from src.ui.bridge import BridgeHost

logger = logging.getLogger(__name__)


def wire_settings_events(
    bridge: BridgeHost,
    on_settings_changed: Callable[[dict], None] | None = None,
) -> None:
    """Connect settings bridge events between JS and Python.

    Registers handlers on *bridge* for ``settings.load`` and ``settings.save``
    events that the React UI can emit, and uses ``bridge.emit`` to push
    responses back.
    """

    # ------------------------------------------------------------------
    # settings.load  ->  read from config, emit settings.data
    # ------------------------------------------------------------------

    def _on_load(_data: Any) -> None:
        try:
            settings = load_settings()
            bridge.emit("settings.data", settings)
        except Exception:
            logger.exception("Error loading settings")
            bridge.emit("settings.data", {"success": False})

    bridge.on("settings.load", _on_load)

    # ------------------------------------------------------------------
    # settings.save  ->  persist via config, emit settings.saved
    # ------------------------------------------------------------------

    def _on_save(data: Any) -> None:
        try:
            settings = data.get("settings", data)
            save_settings(settings)
            bridge.emit("settings.saved", {"success": True})

            if on_settings_changed is not None:
                on_settings_changed(settings)
        except Exception:
            logger.exception("Error saving settings")
            bridge.emit("settings.saved", {"success": False})

    bridge.on("settings.save", _on_save)

    logger.info("Settings bridge events wired")
