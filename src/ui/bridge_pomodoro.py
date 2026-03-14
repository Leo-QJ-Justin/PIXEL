"""Wire pomodoro-related events between the React UI and the Python backend."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from integrations.pomodoro.integration import PomodoroIntegration
    from src.ui.bridge import BridgeHost

logger = logging.getLogger(__name__)


def wire_pomodoro_events(bridge: BridgeHost, integration: PomodoroIntegration) -> None:
    """Connect pomodoro bridge events between JS and Python.

    Registers handlers on *bridge* for each ``timer.*`` event that the
    React UI can emit, and connects integration signals to push state
    updates back to the JS side.
    """

    # ------------------------------------------------------------------
    # JS -> Python: timer commands
    # ------------------------------------------------------------------

    def _on_start(_data: Any) -> None:
        try:
            integration.start_session()
        except Exception:
            logger.exception("Error starting pomodoro session")

    def _on_pause(_data: Any) -> None:
        try:
            integration.pause()
        except Exception:
            logger.exception("Error pausing pomodoro")

    def _on_skip(_data: Any) -> None:
        try:
            integration.skip()
        except Exception:
            logger.exception("Error skipping pomodoro")

    def _on_start_break(_data: Any) -> None:
        try:
            integration.start_break()
        except Exception:
            logger.exception("Error starting pomodoro break")

    def _on_skip_break(_data: Any) -> None:
        try:
            integration.skip_break()
        except Exception:
            logger.exception("Error skipping pomodoro break")

    bridge.on("timer.start", _on_start)
    bridge.on("timer.pause", _on_pause)
    bridge.on("timer.skip", _on_skip)
    bridge.on("timer.startBreak", _on_start_break)
    bridge.on("timer.skipBreak", _on_skip_break)

    # ------------------------------------------------------------------
    # Python -> JS: integration signals
    # ------------------------------------------------------------------

    def _on_timer_tick(remaining: int) -> None:
        bridge.emit("timer.tick", {"remaining": remaining})

    def _on_state_changed(state: str, context: dict) -> None:
        bridge.emit("timer.state", {"state": state, "context": context})

    def _on_session_completed(completed: int) -> None:
        bridge.emit("pomodoro.session", {"completed": completed})

    def _on_stats_updated(stats: dict) -> None:
        bridge.emit(
            "pomodoro.stats",
            {
                "daily": stats.get("daily", {}),
                "streak": stats.get("current_streak_days", 0),
                "total": stats.get("total_sessions", 0),
                "longest_streak": stats.get("longest_streak_days", 0),
            },
        )

    integration.timer_tick.connect(_on_timer_tick)
    integration.state_changed.connect(_on_state_changed)
    integration.session_completed.connect(_on_session_completed)
    integration.stats_updated.connect(_on_stats_updated)

    logger.info("Pomodoro bridge events wired")
