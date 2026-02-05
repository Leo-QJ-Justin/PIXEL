"""Tests for HaroWidget UI component."""

from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt


@pytest.mark.ui
class TestHaroWidgetInit:
    """Tests for HaroWidget initialization."""

    def test_widget_initializes_without_error(self, qtbot, behavior_registry):
        """Widget should initialize without raising exceptions."""
        # Patch get_behavior_settings to avoid file access
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget is not None

    def test_initial_state_not_alerting(self, qtbot, behavior_registry):
        """Widget should start in non-alerting state."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget._is_alerting is False

    def test_initial_state_not_wandering(self, qtbot, behavior_registry):
        """Widget should start in non-wandering state."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget._is_wandering is False

    def test_starts_with_idle_behavior(self, qtbot, behavior_registry):
        """Widget should trigger idle behavior on init."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert behavior_registry.current == "idle"


@pytest.mark.ui
class TestHaroWidgetWindowFlags:
    """Tests for HaroWidget window configuration."""

    def test_window_is_frameless(self, qtbot, behavior_registry):
        """Window should have frameless hint."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

        flags = widget.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_window_stays_on_top(self, qtbot, behavior_registry):
        """Window should have stay-on-top hint."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

        flags = widget.windowFlags()
        assert flags & Qt.WindowType.WindowStaysOnTopHint

    def test_window_is_tool(self, qtbot, behavior_registry):
        """Window should have tool hint (no taskbar entry)."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

        flags = widget.windowFlags()
        assert flags & Qt.WindowType.Tool


@pytest.mark.ui
class TestHaroWidgetAlert:
    """Tests for HaroWidget alert functionality."""

    def test_trigger_alert_sets_alerting_state(self, qtbot, behavior_registry):
        """trigger_alert should set _is_alerting to True."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

            widget.trigger_alert("Test User")

        assert widget._is_alerting is True

    def test_stop_alert_clears_alerting_state(self, qtbot, behavior_registry):
        """stop_alert should set _is_alerting to False."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

            widget.trigger_alert("Test User")
            widget.stop_alert()

        assert widget._is_alerting is False

    def test_trigger_alert_while_alerting_does_nothing(self, qtbot, behavior_registry):
        """Calling trigger_alert while already alerting should not restart alert."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

            widget.trigger_alert("User 1")
            widget.trigger_alert("User 2")

        # Should still be alerting (second call was ignored)
        assert widget._is_alerting is True

    def test_alert_triggers_alert_behavior(self, qtbot, behavior_registry):
        """trigger_alert should switch to alert behavior."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

            widget.trigger_alert("Test User")

        assert behavior_registry.current == "alert"

    def test_stop_alert_returns_to_idle(self, qtbot, behavior_registry):
        """stop_alert should return to idle behavior."""
        with patch("src.ui.haro_window.get_behavior_settings", return_value={}):
            from src.ui.haro_window import HaroWidget

            widget = HaroWidget(behavior_registry)
            qtbot.addWidget(widget)

            widget.trigger_alert("Test User")
            widget.stop_alert()

        assert behavior_registry.current == "idle"


@pytest.mark.ui
class TestBehaviorRegistry:
    """Tests for BehaviorRegistry integration."""

    def test_behavior_registry_discovers_behaviors(self, behavior_registry):
        """Registry should discover all test behaviors."""
        behaviors = behavior_registry.list_behaviors()
        assert "idle" in behaviors
        assert "alert" in behaviors
        assert "wander" in behaviors

    def test_behavior_has_correct_priority(self, behavior_registry):
        """Behaviors should have correct priority values."""
        idle = behavior_registry.get_behavior("idle")
        alert = behavior_registry.get_behavior("alert")
        wander = behavior_registry.get_behavior("wander")

        assert idle.priority == 0
        assert alert.priority == 10
        assert wander.priority == 5

    def test_behavior_has_sprites(self, behavior_registry):
        """Behaviors should have loaded sprites."""
        idle = behavior_registry.get_behavior("idle")
        alert = behavior_registry.get_behavior("alert")
        wander = behavior_registry.get_behavior("wander")

        assert len(idle.sprites) == 2
        assert len(alert.sprites) == 2
        assert len(wander.sprites) == 4
