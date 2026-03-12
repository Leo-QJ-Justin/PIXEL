"""Tests for Google Calendar settings UI builder."""

import copy
from unittest.mock import patch

from PyQt6.QtWidgets import QCheckBox, QPushButton, QSlider, QWidget

import config


def _make_pending():
    return copy.deepcopy(config.DEFAULT_SETTINGS)


class TestGCalSettingsUI:
    def test_returns_list_of_widgets(self, qtbot):
        from integrations.google_calendar.settings_ui import build_settings_sections

        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            sections = build_settings_sections(pending, font="sans-serif")
        assert isinstance(sections, list)
        assert len(sections) >= 1
        for s in sections:
            assert isinstance(s, QWidget)

    def test_has_connect_button_when_not_authenticated(self, qtbot):
        from integrations.google_calendar.settings_ui import build_settings_sections

        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            sections = build_settings_sections(pending, font="sans-serif")
        for s in sections:
            qtbot.addWidget(s)
            s.show()
        all_btns = []
        for s in sections:
            all_btns.extend(s.findChildren(QPushButton))
        connect_btns = [b for b in all_btns if "Connect" in b.text()]
        assert len(connect_btns) == 1
        assert connect_btns[0].isVisible()

    def test_has_reminder_checkboxes(self, qtbot):
        from integrations.google_calendar.settings_ui import build_settings_sections

        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            sections = build_settings_sections(pending, font="sans-serif")
        all_cbs = []
        for s in sections:
            qtbot.addWidget(s)
            all_cbs.extend(s.findChildren(QCheckBox))
        reminder_cbs = [
            cb
            for cb in all_cbs
            if "minutes before" in cb.text() or "event start" in cb.text().lower()
        ]
        assert len(reminder_cbs) == 3

    def test_has_check_interval_slider(self, qtbot):
        from integrations.google_calendar.settings_ui import build_settings_sections

        pending = _make_pending()
        with patch(
            "integrations.google_calendar.settings_ui.is_authenticated",
            return_value=False,
        ):
            sections = build_settings_sections(pending, font="sans-serif")
        all_sliders = []
        for s in sections:
            qtbot.addWidget(s)
            all_sliders.extend(s.findChildren(QSlider))
        interval_slider = [s for s in all_sliders if s.maximum() == 15]
        assert len(interval_slider) == 1
