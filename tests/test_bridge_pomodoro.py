"""Tests for bridge_pomodoro event wiring."""

import json
from unittest.mock import MagicMock

import pytest

from src.ui.bridge import BridgeHost
from src.ui.bridge_pomodoro import wire_pomodoro_events


def _make_bridge_and_capture():
    """Create a BridgeHost with a JS callback that captures emitted events."""
    bridge = BridgeHost()
    emitted: list[tuple[str, object]] = []

    def _capture(event: str, payload_json: str):
        emitted.append((event, json.loads(payload_json)))

    bridge.register_js_callback(_capture)
    return bridge, emitted


def _make_mock_integration():
    """Build a mock PomodoroIntegration with connectable signals."""
    integration = MagicMock()
    # Signals are mocked as MagicMock by default, so .connect works
    return integration


@pytest.mark.unit
class TestCommandForwarding:
    """JS -> Python: timer commands are forwarded to integration."""

    def test_start_calls_start_session(self):
        bridge, _emitted = _make_bridge_and_capture()
        integration = _make_mock_integration()

        wire_pomodoro_events(bridge, integration)
        bridge.receive("timer.start", json.dumps({}))

        integration.start_session.assert_called_once()

    def test_pause_calls_pause(self):
        bridge, _emitted = _make_bridge_and_capture()
        integration = _make_mock_integration()

        wire_pomodoro_events(bridge, integration)
        bridge.receive("timer.pause", json.dumps({}))

        integration.pause.assert_called_once()

    def test_skip_calls_skip(self):
        bridge, _emitted = _make_bridge_and_capture()
        integration = _make_mock_integration()

        wire_pomodoro_events(bridge, integration)
        bridge.receive("timer.skip", json.dumps({}))

        integration.skip.assert_called_once()

    def test_start_break_calls_start_break(self):
        bridge, _emitted = _make_bridge_and_capture()
        integration = _make_mock_integration()

        wire_pomodoro_events(bridge, integration)
        bridge.receive("timer.startBreak", json.dumps({}))

        integration.start_break.assert_called_once()

    def test_skip_break_calls_skip_break(self):
        bridge, _emitted = _make_bridge_and_capture()
        integration = _make_mock_integration()

        wire_pomodoro_events(bridge, integration)
        bridge.receive("timer.skipBreak", json.dumps({}))

        integration.skip_break.assert_called_once()


@pytest.mark.unit
class TestSignalEmission:
    """Python -> JS: integration signals emit events to the bridge."""

    def test_stats_updated_normalizes_field_names(self):
        bridge, emitted = _make_bridge_and_capture()
        integration = _make_mock_integration()

        # Capture the callback registered via .connect()
        wire_pomodoro_events(bridge, integration)

        # Find the stats_updated handler
        stats_handler = integration.stats_updated.connect.call_args[0][0]
        stats_handler(
            {
                "daily": {"2026-03-14": 3},
                "total_sessions": 10,
                "current_streak_days": 5,
                "longest_streak_days": 7,
            }
        )

        events = {e[0]: e[1] for e in emitted}
        assert "pomodoro.stats" in events
        stats = events["pomodoro.stats"]
        assert stats["daily"] == {"2026-03-14": 3}
        assert stats["streak"] == 5
        assert stats["total"] == 10
        assert stats["longest_streak"] == 7

    def test_timer_tick_emits_remaining(self):
        bridge, emitted = _make_bridge_and_capture()
        integration = _make_mock_integration()

        wire_pomodoro_events(bridge, integration)

        tick_handler = integration.timer_tick.connect.call_args[0][0]
        tick_handler(1200)

        events = {e[0]: e[1] for e in emitted}
        assert "timer.tick" in events
        assert events["timer.tick"]["remaining"] == 1200

    def test_state_changed_emits_state_and_context(self):
        bridge, emitted = _make_bridge_and_capture()
        integration = _make_mock_integration()

        wire_pomodoro_events(bridge, integration)

        state_handler = integration.state_changed.connect.call_args[0][0]
        state_handler("FOCUS", {"previous_state": "IDLE", "remaining_seconds": 1500})

        events = {e[0]: e[1] for e in emitted}
        assert "timer.state" in events
        assert events["timer.state"]["state"] == "FOCUS"
        assert events["timer.state"]["context"]["remaining_seconds"] == 1500
