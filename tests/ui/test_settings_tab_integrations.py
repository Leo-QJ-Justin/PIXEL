"""Tests for the discovery-based integrations tab."""

import copy
from unittest.mock import patch

from PyQt6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QPushButton, QSlider, QSpinBox, QWidget

import config
from src.ui.settings.tab_integrations import build_integrations_tab


def _make_pending():
    return copy.deepcopy(config.DEFAULT_SETTINGS)


class TestIntegrationsTab:
    def test_creates_widget(self, qtbot):
        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        assert isinstance(page, QWidget)

    def test_has_pomodoro_focus_slider(self, qtbot):
        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        sliders = [s for s in page.findChildren(QSlider) if s.maximum() == 120]
        assert len(sliders) == 1
        assert sliders[0].value() == 25

    def test_has_weather_city_input(self, qtbot):
        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        edits = page.findChildren(QLineEdit)
        city_edits = [e for e in edits if e.text() == "New York"]
        assert len(city_edits) == 1

    def test_has_weather_units_combo(self, qtbot):
        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        combos = page.findChildren(QComboBox)
        assert len(combos) >= 1
        items = [combos[0].itemText(i) for i in range(combos[0].count())]
        assert any("Metric" in item for item in items)

    def test_has_calendar_connect_button(self, qtbot):
        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        page.show()
        btns = [b for b in page.findChildren(QPushButton) if "Connect" in b.text()]
        assert len(btns) == 1

    def test_has_sessions_spinbox(self, qtbot):
        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        spins = [s for s in page.findChildren(QSpinBox) if s.maximum() == 12]
        assert len(spins) == 1

    def test_has_reminder_checkboxes(self, qtbot):
        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        reminder_cbs = [
            w
            for w in page.findChildren(QCheckBox)
            if "minutes before" in w.text() or "event start" in w.text().lower()
        ]
        assert len(reminder_cbs) == 3
