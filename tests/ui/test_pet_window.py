"""Tests for PetWidget UI component."""

import copy
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt

from src.core.pet_state import PetState
from src.ui.pet_window import PetWidget

# Default fake settings used by most tests
_DEFAULT_SETTINGS = {
    "user_name": "",
    "general": {},
    "behaviors": {},
    "integrations": {},
}


def _make_settings(**overrides):
    """Build a test settings dict, merging overrides into defaults."""
    settings = copy.deepcopy(_DEFAULT_SETTINGS)
    for key, value in overrides.items():
        if isinstance(value, dict) and key in settings and isinstance(settings[key], dict):
            settings[key].update(value)
        else:
            settings[key] = value
    return settings


def _patch_settings(settings=None):
    """Return a patch context for load_settings used by PetWidget."""
    return patch("src.ui.pet_window.load_settings", return_value=settings or _DEFAULT_SETTINGS)


@pytest.mark.ui
class TestPetWidgetInit:
    """Tests for PetWidget initialization."""

    def test_widget_initializes_without_error(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget is not None

    def test_initial_state_is_idle(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget._state_machine.state == PetState.IDLE

    def test_starts_with_idle_behavior(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert behavior_registry.current == "idle"


@pytest.mark.ui
class TestPetWidgetWindowFlags:
    def test_window_is_frameless(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget.windowFlags() & Qt.WindowType.FramelessWindowHint

    def test_window_stays_on_top(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint

    def test_window_is_tool(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget.windowFlags() & Qt.WindowType.Tool


@pytest.mark.ui
class TestPetWidgetAlert:
    def test_trigger_alert_sets_alerting_state(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("Test User")

        assert widget._state_machine.state == PetState.ALERTING

    def test_stop_alert_clears_alerting_state(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("Test User")
            widget.stop_alert()

        assert widget._state_machine.state == PetState.IDLE

    def test_trigger_alert_while_alerting_does_nothing(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("User 1")
            widget.trigger_alert("User 2")

        assert widget._state_machine.state == PetState.ALERTING

    def test_alert_triggers_alert_behavior(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("Test User")

        assert behavior_registry.current == "alert"

    def test_stop_alert_returns_to_idle(self, qtbot, behavior_registry):
        with _patch_settings():
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("Test User")
            widget.stop_alert()

        assert behavior_registry.current == "idle"


@pytest.mark.ui
class TestWaveGreeting:
    def test_wave_shows_greeting_bubble(self, qtbot, behavior_registry):
        settings = _make_settings(
            general={"speech_bubble": {"enabled": True}},
            behaviors={"wave": {"greeting": "Hello!"}},
        )
        with _patch_settings(settings), patch("os.getlogin", return_value="testuser"):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget._speech_bubble = MagicMock()
            behavior_registry.trigger("wave")

        widget._speech_bubble.show_message.assert_called_once_with("Hello, testuser!", 3000)


@pytest.mark.ui
class TestBehaviorRegistry:
    def test_behavior_registry_discovers_behaviors(self, behavior_registry):
        behaviors = behavior_registry.list_behaviors()
        assert "idle" in behaviors
        assert "alert" in behaviors
        assert "wander" in behaviors

    def test_behavior_has_correct_priority(self, behavior_registry):
        idle = behavior_registry.get_behavior("idle")
        alert = behavior_registry.get_behavior("alert")
        wander = behavior_registry.get_behavior("wander")

        assert idle.priority == 0
        assert alert.priority == 10
        assert wander.priority == 5

    def test_behavior_has_gif_path(self, behavior_registry):
        idle = behavior_registry.get_behavior("idle")
        alert = behavior_registry.get_behavior("alert")
        wander = behavior_registry.get_behavior("wander")

        assert idle.gif_path.exists()
        assert alert.gif_path.exists()
        assert wander.gif_path.exists()


@pytest.mark.ui
class TestTimePeriodTransition:
    def _make_widget(
        self, qtbot, behavior_registry, behavior_overrides=None, general_overrides=None
    ):
        behaviors = behavior_overrides or {}
        general = general_overrides or {}
        settings = _make_settings(behaviors=behaviors, general=general)

        with _patch_settings(settings):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
        return widget

    def test_initial_period_is_set(self, qtbot, behavior_registry):
        widget = self._make_widget(
            qtbot,
            behavior_registry,
            behavior_overrides={
                "time_periods": {
                    "enabled": True,
                    "check_interval_ms": 30000,
                    "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                    "greetings": {},
                }
            },
        )
        assert widget._last_time_period is not None

    def test_no_trigger_on_same_period(self, qtbot, behavior_registry):
        widget = self._make_widget(
            qtbot,
            behavior_registry,
            behavior_overrides={
                "time_periods": {
                    "enabled": True,
                    "check_interval_ms": 30000,
                    "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                    "greetings": {"morning": "Good morning!"},
                }
            },
        )
        widget._speech_bubble = MagicMock()

        widget._check_time_period_transition()
        widget._speech_bubble.show_message.assert_not_called()

    def test_transition_triggers_greeting(self, qtbot, behavior_registry):
        widget = self._make_widget(
            qtbot,
            behavior_registry,
            behavior_overrides={
                "time_periods": {
                    "enabled": True,
                    "check_interval_ms": 30000,
                    "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                    "greetings": {"morning": "Good morning!"},
                }
            },
            general_overrides={"speech_bubble": {"enabled": True, "duration_ms": 3000}},
        )
        widget._speech_bubble = MagicMock()

        widget._last_time_period = "night"
        with patch.object(widget, "_get_current_period", return_value="morning"):
            widget._check_time_period_transition()

        widget._speech_bubble.show_message.assert_called_once()

    def test_transition_shows_bubble_only(self, qtbot, behavior_registry):
        """Time period transition shows greeting bubble without changing behavior."""
        widget = self._make_widget(
            qtbot,
            behavior_registry,
            behavior_overrides={
                "time_periods": {
                    "enabled": True,
                    "check_interval_ms": 30000,
                    "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                    "greetings": {"morning": "Rise and shine!"},
                }
            },
            general_overrides={"speech_bubble": {"enabled": True, "duration_ms": 3000}},
        )
        widget._speech_bubble = MagicMock()

        widget._last_time_period = "night"
        with patch.object(widget, "_get_current_period", return_value="morning"):
            widget._check_time_period_transition()

        widget._speech_bubble.show_message.assert_called_once()
        assert behavior_registry.current == "idle"  # behavior unchanged

    def test_no_trigger_when_sleeping(self, qtbot, behavior_registry):
        widget = self._make_widget(
            qtbot,
            behavior_registry,
            behavior_overrides={
                "time_periods": {
                    "enabled": True,
                    "check_interval_ms": 30000,
                    "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                    "greetings": {"morning": "Good morning!"},
                }
            },
        )
        widget._speech_bubble = MagicMock()
        widget._state_machine.force(PetState.SLEEPING)

        widget._last_time_period = "night"
        with patch.object(widget, "_get_current_period", return_value="morning"):
            widget._check_time_period_transition()

        widget._speech_bubble.show_message.assert_not_called()

    def test_disabled_time_periods_no_timer(self, qtbot, behavior_registry):
        widget = self._make_widget(
            qtbot,
            behavior_registry,
            behavior_overrides={
                "time_periods": {
                    "enabled": False,
                    "periods": {"morning": "06:00"},
                    "greetings": {},
                }
            },
        )
        assert not widget._time_period_timer.isActive()
