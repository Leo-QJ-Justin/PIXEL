"""Tests for HaroWidget UI component."""

from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt

# Import the module so patch() can resolve it
import src.ui.haro_window  # noqa: F401


@pytest.fixture
def mock_config_paths(mock_sprites_dir, mock_sounds_dir):
    """Patch config module paths to use test directories."""
    with patch.object(src.ui.haro_window, "SPRITES_DIR", mock_sprites_dir):
        with patch.object(src.ui.haro_window, "SOUNDS_DIR", mock_sounds_dir):
            yield


@pytest.mark.ui
class TestHaroWidgetInit:
    """Tests for HaroWidget initialization."""

    def test_widget_initializes_without_error(self, qtbot, mock_config_paths):
        """Widget should initialize without raising exceptions."""
        from src.ui.haro_window import HaroWidget

        widget = HaroWidget()
        qtbot.addWidget(widget)

        assert widget is not None

    def test_initial_state_not_alerting(self, qtbot, mock_config_paths):
        """Widget should start in non-alerting state."""
        from src.ui.haro_window import HaroWidget

        widget = HaroWidget()
        qtbot.addWidget(widget)

        assert widget._is_alerting is False

    def test_initial_state_not_wandering(self, qtbot, mock_config_paths):
        """Widget should start in non-wandering state."""
        from src.ui.haro_window import HaroWidget

        widget = HaroWidget()
        qtbot.addWidget(widget)

        assert widget._is_wandering is False


@pytest.mark.ui
class TestHaroWidgetWindowFlags:
    """Tests for HaroWidget window configuration."""

    def test_window_is_frameless(self, qtbot, mock_config_paths):
        """Window should have frameless hint."""
        from src.ui.haro_window import HaroWidget

        widget = HaroWidget()
        qtbot.addWidget(widget)

        flags = widget.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_window_stays_on_top(self, qtbot, mock_config_paths):
        """Window should have stay-on-top hint."""
        from src.ui.haro_window import HaroWidget

        widget = HaroWidget()
        qtbot.addWidget(widget)

        flags = widget.windowFlags()
        assert flags & Qt.WindowType.WindowStaysOnTopHint

    def test_window_is_tool(self, qtbot, mock_config_paths):
        """Window should have tool hint (no taskbar entry)."""
        from src.ui.haro_window import HaroWidget

        widget = HaroWidget()
        qtbot.addWidget(widget)

        flags = widget.windowFlags()
        assert flags & Qt.WindowType.Tool


@pytest.mark.ui
class TestHaroWidgetAlert:
    """Tests for HaroWidget alert functionality."""

    def test_trigger_alert_sets_alerting_state(self, qtbot, mock_config_paths):
        """trigger_alert should set _is_alerting to True."""
        from src.ui.haro_window import HaroWidget

        widget = HaroWidget()
        qtbot.addWidget(widget)

        widget.trigger_alert("Test User")

        assert widget._is_alerting is True

    def test_stop_alert_clears_alerting_state(self, qtbot, mock_config_paths):
        """stop_alert should set _is_alerting to False."""
        from src.ui.haro_window import HaroWidget

        widget = HaroWidget()
        qtbot.addWidget(widget)

        widget.trigger_alert("Test User")
        widget.stop_alert()

        assert widget._is_alerting is False

    def test_trigger_alert_while_alerting_does_nothing(self, qtbot, mock_config_paths):
        """Calling trigger_alert while already alerting should not restart alert."""
        from src.ui.haro_window import HaroWidget

        widget = HaroWidget()
        qtbot.addWidget(widget)

        widget.trigger_alert("User 1")
        widget.trigger_alert("User 2")

        # Should still be alerting (second call was ignored)
        assert widget._is_alerting is True
