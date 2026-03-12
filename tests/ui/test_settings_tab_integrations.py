import copy
from unittest.mock import patch

from PyQt6.QtWidgets import QCheckBox, QPushButton, QSlider, QSpinBox, QWidget

import config
from src.ui.settings.tab_integrations import build_integrations_tab


def _make_pending():
    return copy.deepcopy(config.DEFAULT_SETTINGS)


class TestIntegrationsTab:
    def test_creates_widget(self, qtbot):
        pending = _make_pending()
        with patch("src.ui.settings.tab_integrations.is_authenticated", return_value=False):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        assert isinstance(page, QWidget)

    def test_has_focus_slider(self, qtbot):
        pending = _make_pending()
        with patch("src.ui.settings.tab_integrations.is_authenticated", return_value=False):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        slider = None
        for w in page.findChildren(QSlider):
            if w.maximum() == 120:
                slider = w
                break
        assert slider is not None
        assert slider.value() == 25

    def test_focus_slider_updates_pending(self, qtbot):
        pending = _make_pending()
        with patch("src.ui.settings.tab_integrations.is_authenticated", return_value=False):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        slider = None
        for w in page.findChildren(QSlider):
            if w.maximum() == 120:
                slider = w
                break
        slider.setValue(45)
        assert pending["integrations"]["pomodoro"]["work_duration_minutes"] == 45

    def test_has_calendar_connect_button(self, qtbot):
        pending = _make_pending()
        with patch("src.ui.settings.tab_integrations.is_authenticated", return_value=False):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        page.show()
        btn = None
        for w in page.findChildren(QPushButton):
            if "Connect" in w.text():
                btn = w
                break
        assert btn is not None
        assert btn.isVisible()

    def test_sessions_per_cycle_spinbox(self, qtbot):
        pending = _make_pending()
        with patch("src.ui.settings.tab_integrations.is_authenticated", return_value=False):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        spin = None
        for w in page.findChildren(QSpinBox):
            if w.maximum() == 12:
                spin = w
                break
        assert spin is not None
        assert spin.value() == 4

    def test_reminder_checkboxes(self, qtbot):
        pending = _make_pending()
        with patch("src.ui.settings.tab_integrations.is_authenticated", return_value=False):
            page = build_integrations_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        reminder_cbs = [
            w
            for w in page.findChildren(QCheckBox)
            if "minutes before" in w.text() or "event start" in w.text().lower()
        ]
        assert len(reminder_cbs) == 3
