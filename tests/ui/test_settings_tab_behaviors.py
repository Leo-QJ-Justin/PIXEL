import copy

from PyQt6.QtWidgets import QCheckBox, QLineEdit, QSlider, QSpinBox, QWidget

import config
from src.ui.settings.tab_behaviors import build_behaviors_tab


def _make_pending():
    return copy.deepcopy(config.DEFAULT_SETTINGS)


class TestBehaviorsTab:
    def test_creates_widget(self, qtbot):
        pending = _make_pending()
        page = build_behaviors_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        assert isinstance(page, QWidget)

    def test_has_wander_chance_slider(self, qtbot):
        pending = _make_pending()
        page = build_behaviors_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        slider = None
        for w in page.findChildren(QSlider):
            if w.maximum() == 100:
                slider = w
                break
        assert slider is not None
        assert slider.value() == 30  # 0.3 * 100

    def test_wander_chance_updates_pending(self, qtbot):
        pending = _make_pending()
        page = build_behaviors_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        slider = None
        for w in page.findChildren(QSlider):
            if w.maximum() == 100:
                slider = w
                break
        slider.setValue(50)
        assert pending["behaviors"]["wander"]["wander_chance"] == 0.5

    def test_has_wave_greeting(self, qtbot):
        pending = _make_pending()
        page = build_behaviors_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        edit = None
        for w in page.findChildren(QLineEdit):
            if w.text() == "Hello!":
                edit = w
                break
        assert edit is not None

    def test_has_encouraging_enable(self, qtbot):
        pending = _make_pending()
        page = build_behaviors_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        cb = None
        for w in page.findChildren(QCheckBox):
            if "Encouraging" in w.text():
                cb = w
                break
        assert cb is not None

    def test_has_trigger_checkboxes(self, qtbot):
        pending = _make_pending()
        page = build_behaviors_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        triggers = [
            w
            for w in page.findChildren(QCheckBox)
            if any(t in w.text() for t in ["Restless", "Proud", "Curious"])
        ]
        assert len(triggers) >= 3

    def test_cooldown_slider_updates_pending(self, qtbot):
        pending = _make_pending()
        page = build_behaviors_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        slider = None
        for w in page.findChildren(QSlider):
            if w.minimum() == 15 and w.maximum() == 120:
                slider = w
                break
        assert slider is not None
        slider.setValue(60)
        assert pending["integrations"]["encouraging"]["cooldown_min_minutes"] == 60

    def test_interval_spinboxes(self, qtbot):
        pending = _make_pending()
        page = build_behaviors_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        spins = [w for w in page.findChildren(QSpinBox) if w.maximum() == 60000]
        assert len(spins) == 2  # min and max interval
