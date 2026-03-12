"""Tests for Pomodoro settings UI builder."""

import copy

from PyQt6.QtWidgets import QCheckBox, QSlider, QSpinBox, QWidget

import config


def _make_pending():
    return copy.deepcopy(config.DEFAULT_SETTINGS)


class TestPomodoroSettingsUI:
    def test_returns_list_of_widgets(self, qtbot):
        from integrations.pomodoro.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        assert isinstance(sections, list)
        assert len(sections) >= 1
        for s in sections:
            assert isinstance(s, QWidget)

    def test_has_focus_slider(self, qtbot):
        from integrations.pomodoro.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        all_sliders = []
        for s in sections:
            qtbot.addWidget(s)
            all_sliders.extend(s.findChildren(QSlider))
        focus_slider = [s for s in all_sliders if s.maximum() == 120]
        assert len(focus_slider) == 1
        assert focus_slider[0].value() == 25

    def test_focus_slider_updates_pending(self, qtbot):
        from integrations.pomodoro.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        for s in sections:
            qtbot.addWidget(s)
        sliders = []
        for s in sections:
            sliders.extend(s.findChildren(QSlider))
        focus_slider = [s for s in sliders if s.maximum() == 120][0]
        focus_slider.setValue(45)
        assert pending["integrations"]["pomodoro"]["work_duration_minutes"] == 45

    def test_has_sessions_spinbox(self, qtbot):
        from integrations.pomodoro.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        all_spins = []
        for s in sections:
            qtbot.addWidget(s)
            all_spins.extend(s.findChildren(QSpinBox))
        cycle_spin = [s for s in all_spins if s.maximum() == 12]
        assert len(cycle_spin) == 1
        assert cycle_spin[0].value() == 4

    def test_has_auto_start_checkbox(self, qtbot):
        from integrations.pomodoro.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        all_cbs = []
        for s in sections:
            qtbot.addWidget(s)
            all_cbs.extend(s.findChildren(QCheckBox))
        auto_start = [cb for cb in all_cbs if "auto-start" in cb.text().lower()]
        assert len(auto_start) == 1
