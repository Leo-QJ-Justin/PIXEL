"""Tests for the MapleStory-themed SettingsDialog."""

import json
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QListWidget,
    QSlider,
    QSpinBox,
    QTimeEdit,
)

# Required for patching — see MEMORY.md gotcha about Python 3.14 mock.patch
import config  # noqa: F401
import src.ui.settings_dialog  # noqa: F401
from src.ui.settings_dialog import SettingsDialog

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dialog(qtbot, tmp_path, overrides=None):
    """Create a SettingsDialog backed by a temp settings file."""
    settings_file = tmp_path / "settings.json"
    data = overrides or {}
    settings_file.write_text(json.dumps(data))

    with patch("config.SETTINGS_FILE", settings_file):
        dialog = SettingsDialog()
    qtbot.addWidget(dialog)
    return dialog, settings_file


def _find_widget(dialog, widget_type, match_fn):
    """Find a child widget by type and predicate."""
    for w in dialog.findChildren(widget_type):
        if match_fn(w):
            return w
    return None


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


@pytest.mark.ui
class TestSettingsDialogInit:
    """Dialog should initialize correctly from settings."""

    def test_creates_without_error(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        assert dialog is not None

    def test_has_four_sidebar_tabs(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        sidebar = dialog.findChild(QListWidget)
        assert sidebar.count() == 4

    def test_is_frameless(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint

    def test_is_application_modal(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        assert dialog.windowModality() == Qt.WindowModality.ApplicationModal

    def test_loads_user_name(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path, {"user_name": "Maple"})
        edit = _find_widget(dialog, QLineEdit, lambda w: w.text() == "Maple")
        assert edit is not None

    def test_loads_always_on_top(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path, {"general": {"always_on_top": False}})
        cb = _find_widget(dialog, QCheckBox, lambda w: "Always on top" in w.text())
        assert cb is not None
        assert cb.isChecked() is False

    def test_loads_wander_chance(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path, {"behaviors": {"fly": {"wander_chance": 0.7}}})
        slider = _find_widget(dialog, QSlider, lambda w: w.value() == 70)
        assert slider is not None


# ---------------------------------------------------------------------------
# Editing controls updates _pending
# ---------------------------------------------------------------------------


@pytest.mark.ui
class TestSettingsEditing:
    """Changing form controls should update the pending settings buffer."""

    def test_edit_user_name(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        edit = _find_widget(dialog, QLineEdit, lambda w: w.placeholderText() == "Enter username...")
        edit.setText("NewUser")
        assert dialog._pending["user_name"] == "NewUser"

    def test_toggle_always_on_top(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        cb = _find_widget(dialog, QCheckBox, lambda w: "Always on top" in w.text())
        original = cb.isChecked()
        cb.setChecked(not original)
        assert dialog._pending["general"]["always_on_top"] is not original

    def test_toggle_start_minimized(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        cb = _find_widget(dialog, QCheckBox, lambda w: "Start minimized" in w.text())
        cb.setChecked(True)
        assert dialog._pending["general"]["start_minimized"] is True

    def test_change_facing_direction(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        combo = _find_widget(dialog, QComboBox, lambda w: w.findData("left") >= 0)
        # Switch to "Left"
        combo.setCurrentIndex(combo.findData("left"))
        assert dialog._pending["general"]["sprite_default_facing"] == "left"

    def test_toggle_speech_bubble(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        # Multiple "Enabled" checkboxes exist — find the one that controls
        # speech_bubble by toggling each and checking the pending value.
        cbs = [w for w in dialog.findChildren(QCheckBox) if w.text() == "Enabled"]
        found = False
        for cb in cbs:
            was = dialog._pending["general"]["speech_bubble"]["enabled"]
            cb.setChecked(not cb.isChecked())
            now = dialog._pending["general"]["speech_bubble"]["enabled"]
            if was != now:
                # This is the speech bubble checkbox — verify it toggled
                assert now is not was
                found = True
                break
            # Undo if it wasn't the right one
            cb.setChecked(not cb.isChecked())
        assert found, "Could not find the speech bubble Enabled checkbox"

    def test_change_speech_duration(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        # The duration slider defaults to 3000
        slider = _find_widget(dialog, QSlider, lambda w: w.maximum() == 10000)
        slider.setValue(5000)
        assert dialog._pending["general"]["speech_bubble"]["duration_ms"] == 5000

    def test_change_wander_chance(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        # Wander chance slider has range 0-100
        slider = _find_widget(dialog, QSlider, lambda w: w.maximum() == 100)
        slider.setValue(50)
        assert dialog._pending["behaviors"]["fly"]["wander_chance"] == 0.5

    def test_change_wander_interval_min(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        # Switch to Behaviors tab
        sidebar = dialog.findChild(QListWidget)
        sidebar.setCurrentRow(1)
        # Find the min spinbox (value 5000)
        spin = _find_widget(dialog, QSpinBox, lambda w: w.value() == 5000 and w.maximum() == 60000)
        spin.setValue(8000)
        assert dialog._pending["behaviors"]["fly"]["wander_interval_min_ms"] == 8000

    def test_change_wave_greeting(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        # Find greeting input (default "Hello!")
        edit = _find_widget(dialog, QLineEdit, lambda w: w.text() == "Hello!")
        edit.setText("Hi there!")
        assert dialog._pending["behaviors"]["wave"]["greeting"] == "Hi there!"

    def test_change_sleep_schedule_enabled(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        cb = _find_widget(dialog, QCheckBox, lambda w: "Enable Schedule" in w.text())
        cb.setChecked(True)
        assert dialog._pending["behaviors"]["sleep"]["schedule_enabled"] is True

    def test_change_sleep_start_time(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        # Find a QTimeEdit showing 22:00
        te = _find_widget(
            dialog,
            QTimeEdit,
            lambda w: w.time() == QTime.fromString("22:00", "HH:mm"),
        )
        assert te is not None
        te.setTime(QTime(23, 30))
        assert dialog._pending["behaviors"]["sleep"]["schedule_start"] == "23:30"

    def test_change_morning_greeting(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        edit = _find_widget(dialog, QLineEdit, lambda w: w.text() == "Good morning!")
        edit.setText("Rise and shine!")
        assert (
            dialog._pending["behaviors"]["time_periods"]["greetings"]["morning"]
            == "Rise and shine!"
        )

    def test_change_weather_city(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        edit = _find_widget(dialog, QLineEdit, lambda w: w.text() == "New York")
        edit.setText("Tokyo")
        assert dialog._pending["integrations"]["weather"]["city"] == "Tokyo"

    def test_change_weather_units(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        combo = _find_widget(dialog, QComboBox, lambda w: w.findData("metric") >= 0)
        combo.setCurrentIndex(combo.findData("metric"))
        assert dialog._pending["integrations"]["weather"]["units"] == "metric"

    def test_toggle_weather_enabled(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path, {"integrations": {"weather": {"enabled": True}}})
        # Find the weather Enabled checkbox (on Integrations tab)
        # There may be multiple "Enabled" checkboxes — get all and check the
        # one bound to weather
        cbs = [w for w in dialog.findChildren(QCheckBox) if w.text() == "Enabled"]
        # Toggle each "Enabled" off, check which updates weather
        for cb in cbs:
            if dialog._pending["integrations"]["weather"]["enabled"]:
                cb.setChecked(False)
                if not dialog._pending["integrations"]["weather"]["enabled"]:
                    break
        assert dialog._pending["integrations"]["weather"]["enabled"] is False

    def test_change_calendar_alert_before(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        # Alert before spinbox (default 30, max 120, has " min" suffix)
        spin = _find_widget(
            dialog,
            QSpinBox,
            lambda w: w.value() == 30 and w.maximum() == 120,
        )
        assert spin is not None
        spin.setValue(15)
        assert dialog._pending["integrations"]["google_calendar"]["alert_before_minutes"] == 15


# ---------------------------------------------------------------------------
# Ok / Cancel behavior
# ---------------------------------------------------------------------------


@pytest.mark.ui
class TestSettingsOkCancel:
    """Ok saves settings and emits signal; Cancel discards."""

    def test_ok_saves_to_file(self, qtbot, tmp_path):
        dialog, settings_file = _make_dialog(qtbot, tmp_path)
        dialog._pending["user_name"] = "Saved!"

        with patch("src.ui.settings_dialog.save_settings") as mock_save:
            dialog._on_ok()
            mock_save.assert_called_once()
            saved = mock_save.call_args[0][0]
            assert saved["user_name"] == "Saved!"

    def test_ok_emits_settings_changed(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        spy = MagicMock()
        dialog.settings_changed.connect(spy)

        with patch("src.ui.settings_dialog.save_settings"):
            dialog._on_ok()

        spy.assert_called_once()
        emitted = spy.call_args[0][0]
        assert "general" in emitted

    def test_cancel_does_not_save(self, qtbot, tmp_path):
        dialog, settings_file = _make_dialog(qtbot, tmp_path)
        dialog._pending["user_name"] = "Unsaved"

        with patch("src.ui.settings_dialog.save_settings") as mock_save:
            dialog.reject()
            mock_save.assert_not_called()

    def test_ok_end_to_end(self, qtbot, tmp_path):
        """Full round-trip: edit a control, click Ok, verify file."""
        dialog, settings_file = _make_dialog(qtbot, tmp_path)

        # Edit the user name
        edit = _find_widget(
            dialog,
            QLineEdit,
            lambda w: w.placeholderText() == "Enter username...",
        )
        edit.setText("EndToEnd")

        # Patch save to write to our temp file
        with patch("config.SETTINGS_FILE", settings_file):
            dialog._on_ok()

        saved = json.loads(settings_file.read_text())
        assert saved["user_name"] == "EndToEnd"


# ---------------------------------------------------------------------------
# Nested helper methods
# ---------------------------------------------------------------------------


@pytest.mark.ui
class TestSettingsHelpers:
    """Test _set_nested and _get_nested utilities."""

    def test_set_nested_top_level(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        dialog._set_nested(["user_name"], "test")
        assert dialog._pending["user_name"] == "test"

    def test_set_nested_deep(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        dialog._set_nested(["behaviors", "fly", "wander_chance"], 0.99)
        assert dialog._pending["behaviors"]["fly"]["wander_chance"] == 0.99

    def test_get_nested_returns_value(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path, {"general": {"always_on_top": False}})
        assert dialog._get_nested(["general", "always_on_top"]) is False

    def test_get_nested_returns_default(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        result = dialog._get_nested(["nonexistent", "key"], "fallback")
        assert result == "fallback"

    def test_set_nested_creates_intermediate_dicts(self, qtbot, tmp_path):
        dialog, _ = _make_dialog(qtbot, tmp_path)
        dialog._set_nested(["a", "b", "c"], 42)
        assert dialog._pending["a"]["b"]["c"] == 42
