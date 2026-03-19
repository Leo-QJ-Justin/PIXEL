import copy

from PyQt6.QtWidgets import QCheckBox, QLineEdit, QSlider, QSpinBox, QWidget

import config
from src.ui.settings.tab_general import build_general_tab


def _make_pending():
    return copy.deepcopy(config.DEFAULT_SETTINGS)


class TestGeneralTab:
    def test_creates_widget(self, qtbot):
        pending = _make_pending()
        page = build_general_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        assert isinstance(page, QWidget)

    def test_has_user_name_input(self, qtbot):
        pending = _make_pending()
        pending["user_name"] = "TestUser"
        page = build_general_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        edit = None
        for w in page.findChildren(QLineEdit):
            if w.text() == "TestUser":
                edit = w
                break
        assert edit is not None

    def test_edit_user_name_updates_pending(self, qtbot):
        pending = _make_pending()
        page = build_general_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        edit = None
        for w in page.findChildren(QLineEdit):
            if w.placeholderText() == "Enter username...":
                edit = w
                break
        edit.setText("NewName")
        assert pending["user_name"] == "NewName"

    def test_has_always_on_top_checkbox(self, qtbot):
        pending = _make_pending()
        page = build_general_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        cb = None
        for w in page.findChildren(QCheckBox):
            if "Always on top" in w.text():
                cb = w
                break
        assert cb is not None

    def test_has_sleep_schedule_checkbox(self, qtbot):
        pending = _make_pending()
        page = build_general_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        cb = None
        for w in page.findChildren(QCheckBox):
            if "Enable Schedule" in w.text():
                cb = w
                break
        assert cb is not None

    def test_has_time_greetings(self, qtbot):
        pending = _make_pending()
        page = build_general_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        greetings = [
            w
            for w in page.findChildren(QLineEdit)
            if w.text() in ("Rise and shine!", "Lunch time~", "Sleepy time~")
        ]
        assert len(greetings) == 3

    def test_speech_duration_slider_updates_pending(self, qtbot):
        pending = _make_pending()
        page = build_general_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        slider = None
        for w in page.findChildren(QSlider):
            if w.maximum() == 10000:
                slider = w
                break
        assert slider is not None
        slider.setValue(5000)
        assert pending["general"]["speech_bubble"]["duration_ms"] == 5000

    def test_inactivity_timeout_spinbox(self, qtbot):
        pending = _make_pending()
        page = build_general_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        spin = None
        for w in page.findChildren(QSpinBox):
            if w.maximum() == 3600000:
                spin = w
                break
        assert spin is not None
