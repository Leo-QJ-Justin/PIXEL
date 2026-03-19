"""Tests for BridgeHost event bus."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.ui.bridge import BridgeHost


@pytest.mark.unit
class TestBridgeHostOn:
    """Tests for handler registration via on()."""

    def test_register_handler(self):
        """on() should register a handler for the given event."""
        bridge = BridgeHost()
        handler = MagicMock()

        bridge.on("test.event", handler)

        assert handler in bridge._handlers["test.event"]

    def test_multiple_handlers_for_same_event(self):
        """on() should support multiple handlers per event."""
        bridge = BridgeHost()
        handler_a = MagicMock()
        handler_b = MagicMock()

        bridge.on("test.event", handler_a)
        bridge.on("test.event", handler_b)

        assert len(bridge._handlers["test.event"]) == 2
        assert handler_a in bridge._handlers["test.event"]
        assert handler_b in bridge._handlers["test.event"]


@pytest.mark.unit
class TestBridgeHostReceive:
    """Tests for receive() — JS -> Python dispatch."""

    def test_dispatches_to_registered_handler(self):
        """receive() should parse JSON and call matching handler."""
        bridge = BridgeHost()
        handler = MagicMock()
        bridge.on("greet", handler)

        bridge.receive("greet", json.dumps({"name": "Haro"}))

        handler.assert_called_once_with({"name": "Haro"})

    def test_handler_not_called_for_other_events(self):
        """Handler registered for event A should not fire for event B."""
        bridge = BridgeHost()
        handler = MagicMock()
        bridge.on("event.a", handler)

        bridge.receive("event.b", json.dumps({"x": 1}))

        handler.assert_not_called()

    def test_multiple_handlers_all_called(self):
        """All handlers for an event should be called in order."""
        bridge = BridgeHost()
        call_order = []
        handler_a = MagicMock(side_effect=lambda d: call_order.append("a"))
        handler_b = MagicMock(side_effect=lambda d: call_order.append("b"))
        bridge.on("test", handler_a)
        bridge.on("test", handler_b)

        bridge.receive("test", json.dumps({"v": 42}))

        handler_a.assert_called_once_with({"v": 42})
        handler_b.assert_called_once_with({"v": 42})
        assert call_order == ["a", "b"]

    def test_invalid_json_logs_warning(self):
        """receive() with invalid JSON should log a warning and not crash."""
        bridge = BridgeHost()
        handler = MagicMock()
        bridge.on("test", handler)

        with patch("src.ui.bridge.logger") as mock_logger:
            bridge.receive("test", "not-valid-json{{{")

        handler.assert_not_called()
        mock_logger.warning.assert_called_once()

    def test_none_payload_logs_warning(self):
        """receive() with None payload should log a warning and not crash."""
        bridge = BridgeHost()
        handler = MagicMock()
        bridge.on("test", handler)

        with patch("src.ui.bridge.logger") as mock_logger:
            bridge.receive("test", None)

        handler.assert_not_called()
        mock_logger.warning.assert_called_once()

    def test_handler_exception_is_logged_not_propagated(self):
        """If a handler raises, the exception is logged but does not propagate."""
        bridge = BridgeHost()
        bad_handler = MagicMock(side_effect=ValueError("boom"))
        good_handler = MagicMock()
        bridge.on("test", bad_handler)
        bridge.on("test", good_handler)

        with patch("src.ui.bridge.logger") as mock_logger:
            # Should not raise
            bridge.receive("test", json.dumps({"k": "v"}))

        bad_handler.assert_called_once()
        good_handler.assert_called_once_with({"k": "v"})
        mock_logger.exception.assert_called_once()

    def test_receive_with_no_handlers_is_noop(self):
        """receive() for an event with no handlers should silently do nothing."""
        bridge = BridgeHost()

        # Should not raise
        bridge.receive("unknown.event", json.dumps({"a": 1}))


@pytest.mark.unit
class TestBridgeHostEmit:
    """Tests for emit() — Python -> JS dispatch."""

    def test_emit_calls_js_callback(self):
        """emit() should call the registered JS callback with event and JSON payload."""
        bridge = BridgeHost()
        js_cb = MagicMock()
        bridge.register_js_callback(js_cb)

        bridge.emit("panel.open", {"panel": "journal"})

        js_cb.assert_called_once_with("panel.open", json.dumps({"panel": "journal"}))

    def test_emit_without_callback_is_noop(self):
        """emit() without a registered JS callback should not raise."""
        bridge = BridgeHost()

        # Should not raise
        bridge.emit("some.event", {"data": True})

    def test_emit_with_none_data(self):
        """emit() should handle None data by serializing to JSON 'null'."""
        bridge = BridgeHost()
        js_cb = MagicMock()
        bridge.register_js_callback(js_cb)

        bridge.emit("ping")

        js_cb.assert_called_once_with("ping", "null")

    def test_emit_callback_exception_is_logged(self):
        """If the JS callback raises, the exception is logged but does not propagate."""
        bridge = BridgeHost()
        js_cb = MagicMock(side_effect=RuntimeError("channel down"))
        bridge.register_js_callback(js_cb)

        with patch("src.ui.bridge.logger") as mock_logger:
            # Should not raise
            bridge.emit("event", {"x": 1})

        mock_logger.exception.assert_called_once()


@pytest.mark.unit
class TestBridgeHostRegisterJsCallback:
    """Tests for register_js_callback()."""

    def test_replaces_previous_callback(self):
        """Registering a new callback should replace the old one."""
        bridge = BridgeHost()
        cb1 = MagicMock()
        cb2 = MagicMock()

        bridge.register_js_callback(cb1)
        bridge.register_js_callback(cb2)
        bridge.emit("test", {})

        cb1.assert_not_called()
        cb2.assert_called_once()
