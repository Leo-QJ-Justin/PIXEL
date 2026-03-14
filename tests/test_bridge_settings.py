"""Tests for bridge_settings event wiring."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.ui.bridge import BridgeHost
from src.ui.bridge_settings import wire_settings_events


def _make_bridge_and_capture():
    """Create a BridgeHost with a JS callback that captures emitted events."""
    bridge = BridgeHost()
    emitted: list[tuple[str, object]] = []

    def _capture(event: str, payload_json: str):
        emitted.append((event, json.loads(payload_json)))

    bridge.register_js_callback(_capture)
    return bridge, emitted


@pytest.mark.unit
class TestSettingsLoad:
    """settings.load triggers settings.data emission."""

    def test_load_emits_settings_data(self):
        bridge, emitted = _make_bridge_and_capture()
        fake_settings = {"user_name": "Pixel", "general": {"always_on_top": True}}

        with patch("src.ui.bridge_settings.load_settings", return_value=fake_settings):
            wire_settings_events(bridge)
            bridge.receive("settings.load", json.dumps({}))

        events = {e[0]: e[1] for e in emitted}
        assert "settings.data" in events
        assert events["settings.data"]["user_name"] == "Pixel"
        assert events["settings.data"]["general"]["always_on_top"] is True

    def test_load_error_emits_failure(self):
        bridge, emitted = _make_bridge_and_capture()

        with patch(
            "src.ui.bridge_settings.load_settings",
            side_effect=RuntimeError("read error"),
        ):
            wire_settings_events(bridge)
            bridge.receive("settings.load", json.dumps({}))

        events = {e[0]: e[1] for e in emitted}
        assert events["settings.data"]["success"] is False


@pytest.mark.unit
class TestSettingsSave:
    """settings.save persists and emits settings.saved."""

    def test_save_persists_and_emits(self):
        bridge, emitted = _make_bridge_and_capture()
        callback = MagicMock()
        new_settings = {"user_name": "Updated", "general": {"always_on_top": False}}

        with (
            patch("src.ui.bridge_settings.load_settings", return_value={}),
            patch("src.ui.bridge_settings.save_settings") as mock_save,
        ):
            wire_settings_events(bridge, on_settings_changed=callback)
            bridge.receive("settings.save", json.dumps({"settings": new_settings}))

        mock_save.assert_called_once_with(new_settings)
        callback.assert_called_once_with(new_settings)

        events = {e[0]: e[1] for e in emitted}
        assert "settings.saved" in events
        assert events["settings.saved"]["success"] is True

    def test_save_error_emits_failure(self):
        bridge, emitted = _make_bridge_and_capture()

        with (
            patch("src.ui.bridge_settings.load_settings", return_value={}),
            patch(
                "src.ui.bridge_settings.save_settings",
                side_effect=RuntimeError("write failed"),
            ),
        ):
            wire_settings_events(bridge)
            bridge.receive("settings.save", json.dumps({"settings": {"user_name": "X"}}))

        events = {e[0]: e[1] for e in emitted}
        assert events["settings.saved"]["success"] is False
