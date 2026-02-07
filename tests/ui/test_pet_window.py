"""Tests for PetWidget UI component."""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt

from src.ui.pet_window import PetWidget


@pytest.mark.ui
class TestPetWidgetInit:
    """Tests for PetWidget initialization."""

    def test_widget_initializes_without_error(self, qtbot, behavior_registry):
        """Widget should initialize without raising exceptions."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget is not None

    def test_initial_state_not_alerting(self, qtbot, behavior_registry):
        """Widget should start in non-alerting state."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget._is_alerting is False

    def test_initial_state_not_wandering(self, qtbot, behavior_registry):
        """Widget should start in non-wandering state."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert widget._is_wandering is False

    def test_starts_with_idle_behavior(self, qtbot, behavior_registry):
        """Widget should trigger idle behavior on init."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        assert behavior_registry.current == "idle"


@pytest.mark.ui
class TestPetWidgetWindowFlags:
    """Tests for PetWidget window configuration."""

    def test_window_is_frameless(self, qtbot, behavior_registry):
        """Window should have frameless hint."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        flags = widget.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_window_stays_on_top(self, qtbot, behavior_registry):
        """Window should have stay-on-top hint."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        flags = widget.windowFlags()
        assert flags & Qt.WindowType.WindowStaysOnTopHint

    def test_window_is_tool(self, qtbot, behavior_registry):
        """Window should have tool hint (no taskbar entry)."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)

        flags = widget.windowFlags()
        assert flags & Qt.WindowType.Tool


@pytest.mark.ui
class TestPetWidgetAlert:
    """Tests for PetWidget alert functionality."""

    def test_trigger_alert_sets_alerting_state(self, qtbot, behavior_registry):
        """trigger_alert should set _is_alerting to True."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("Test User")

        assert widget._is_alerting is True

    def test_stop_alert_clears_alerting_state(self, qtbot, behavior_registry):
        """stop_alert should set _is_alerting to False."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("Test User")
            widget.stop_alert()

        assert widget._is_alerting is False

    def test_trigger_alert_while_alerting_does_nothing(self, qtbot, behavior_registry):
        """Calling trigger_alert while already alerting should not restart alert."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("User 1")
            widget.trigger_alert("User 2")

        # Should still be alerting (second call was ignored)
        assert widget._is_alerting is True

    def test_alert_triggers_alert_behavior(self, qtbot, behavior_registry):
        """trigger_alert should switch to alert behavior."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("Test User")

        assert behavior_registry.current == "alert"

    def test_stop_alert_returns_to_idle(self, qtbot, behavior_registry):
        """stop_alert should return to idle behavior."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings", return_value={}
        ):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget.trigger_alert("Test User")
            widget.stop_alert()

        assert behavior_registry.current == "idle"


@pytest.mark.ui
class TestWaveGreeting:
    """Tests for wave behavior greeting bubble."""

    def test_wave_shows_greeting_bubble(self, qtbot, behavior_registry):
        """Triggering wave should show a speech bubble with username greeting."""
        with patch("src.ui.pet_window.get_behavior_settings", return_value={}), patch(
            "src.ui.pet_window.get_general_settings",
            return_value={"speech_bubble": {"enabled": True}},
        ), patch("src.ui.pet_window.getpass") as mock_getpass:
            mock_getpass.getuser.return_value = "testuser"
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
            widget._speech_bubble = MagicMock()
            behavior_registry.trigger("wave")

        widget._speech_bubble.show_message.assert_called_once_with("Hello user:testuser", 3000)


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


@pytest.mark.ui
class TestTimePeriodTransition:
    """Tests for time-period transition logic."""

    def _make_widget(
        self, qtbot, behavior_registry, behavior_overrides=None, general_overrides=None
    ):
        """Helper to create a PetWidget with custom settings patches."""
        behavior_settings = behavior_overrides or {}
        general_settings = general_overrides or {}

        def fake_behavior_settings(name):
            return behavior_settings.get(name, {})

        with patch(
            "src.ui.pet_window.get_behavior_settings", side_effect=fake_behavior_settings
        ), patch("src.ui.pet_window.get_general_settings", return_value=general_settings):
            widget = PetWidget(behavior_registry)
            qtbot.addWidget(widget)
        return widget

    def test_initial_period_is_set(self, qtbot, behavior_registry):
        """On init with time_periods enabled, _last_time_period should be set."""
        settings = {
            "time_periods": {
                "enabled": True,
                "check_interval_ms": 30000,
                "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                "greetings": {},
            }
        }
        widget = self._make_widget(qtbot, behavior_registry, behavior_overrides=settings)
        assert widget._last_time_period is not None

    def test_no_trigger_on_same_period(self, qtbot, behavior_registry):
        """No transition should fire if the period hasn't changed."""
        settings = {
            "time_periods": {
                "enabled": True,
                "check_interval_ms": 30000,
                "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                "greetings": {"morning": "Good morning!"},
            }
        }
        widget = self._make_widget(qtbot, behavior_registry, behavior_overrides=settings)
        widget._speech_bubble = MagicMock()

        # Calling check again should not trigger anything (same period)
        widget._check_time_period_transition()
        widget._speech_bubble.show_message.assert_not_called()

    def test_transition_triggers_greeting(self, qtbot, behavior_registry):
        """When period changes, greeting bubble should be shown."""
        settings = {
            "time_periods": {
                "enabled": True,
                "check_interval_ms": 30000,
                "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                "greetings": {"morning": "Good morning!"},
            }
        }
        general = {"speech_bubble": {"enabled": True, "duration_ms": 3000}}
        widget = self._make_widget(
            qtbot, behavior_registry, behavior_overrides=settings, general_overrides=general
        )
        widget._speech_bubble = MagicMock()

        # Force a period change
        widget._last_time_period = "night"
        with patch.object(widget, "_get_current_period", return_value="morning"):
            widget._check_time_period_transition()

        widget._speech_bubble.show_message.assert_called_once()

    def test_transition_triggers_behavior(self, qtbot, behavior_registry):
        """When period changes to 'morning', the morning behavior should be triggered."""
        settings = {
            "time_periods": {
                "enabled": True,
                "check_interval_ms": 30000,
                "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                "greetings": {},
            }
        }
        widget = self._make_widget(qtbot, behavior_registry, behavior_overrides=settings)

        # Force a period change to morning (which exists in mock_behaviors_dir)
        widget._last_time_period = "night"
        with patch.object(widget, "_get_current_period", return_value="morning"):
            widget._check_time_period_transition()

        assert behavior_registry.current == "morning"

    def test_no_trigger_when_sleeping(self, qtbot, behavior_registry):
        """No transition trigger when pet is sleeping."""
        settings = {
            "time_periods": {
                "enabled": True,
                "check_interval_ms": 30000,
                "periods": {"morning": "06:00", "afternoon": "12:00", "night": "20:00"},
                "greetings": {"morning": "Good morning!"},
            }
        }
        widget = self._make_widget(qtbot, behavior_registry, behavior_overrides=settings)
        widget._speech_bubble = MagicMock()
        widget._is_sleeping = True

        widget._last_time_period = "night"
        with patch.object(widget, "_get_current_period", return_value="morning"):
            widget._check_time_period_transition()

        widget._speech_bubble.show_message.assert_not_called()

    def test_disabled_time_periods_no_timer(self, qtbot, behavior_registry):
        """Timer should not start when time_periods is disabled."""
        settings = {
            "time_periods": {
                "enabled": False,
                "periods": {"morning": "06:00"},
                "greetings": {},
            }
        }
        widget = self._make_widget(qtbot, behavior_registry, behavior_overrides=settings)
        assert not widget._time_period_timer.isActive()
