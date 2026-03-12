"""Tests for Weather settings UI builder."""

import copy

from PyQt6.QtWidgets import QComboBox, QLineEdit, QSlider, QWidget

import config


def _make_pending():
    return copy.deepcopy(config.DEFAULT_SETTINGS)


class TestWeatherSettingsUI:
    def test_returns_list_of_widgets(self, qtbot):
        from integrations.weather.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        assert isinstance(sections, list)
        assert len(sections) >= 1
        for s in sections:
            assert isinstance(s, QWidget)

    def test_has_city_line_edit(self, qtbot):
        from integrations.weather.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        all_edits = []
        for s in sections:
            qtbot.addWidget(s)
            all_edits.extend(s.findChildren(QLineEdit))
        assert len(all_edits) >= 1
        city_edit = all_edits[0]
        assert city_edit.text() == "New York"

    def test_city_edit_updates_pending(self, qtbot):
        from integrations.weather.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        for s in sections:
            qtbot.addWidget(s)
        edits = []
        for s in sections:
            edits.extend(s.findChildren(QLineEdit))
        edits[0].setText("Tokyo")
        assert pending["integrations"]["weather"]["city"] == "Tokyo"

    def test_has_units_combobox(self, qtbot):
        from integrations.weather.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        all_combos = []
        for s in sections:
            qtbot.addWidget(s)
            all_combos.extend(s.findChildren(QComboBox))
        assert len(all_combos) >= 1
        units_combo = all_combos[0]
        items = [units_combo.itemText(i) for i in range(units_combo.count())]
        assert "Metric (\u00b0C)" in items
        assert "Imperial (\u00b0F)" in items

    def test_units_combo_updates_pending(self, qtbot):
        from integrations.weather.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        for s in sections:
            qtbot.addWidget(s)
        combos = []
        for s in sections:
            combos.extend(s.findChildren(QComboBox))
        units_combo = combos[0]
        imperial_idx = next(
            i for i in range(units_combo.count()) if "Imperial" in units_combo.itemText(i)
        )
        units_combo.setCurrentIndex(imperial_idx)
        assert pending["integrations"]["weather"]["units"] == "imperial"

    def test_has_check_interval_slider(self, qtbot):
        from integrations.weather.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        all_sliders = []
        for s in sections:
            qtbot.addWidget(s)
            all_sliders.extend(s.findChildren(QSlider))
        interval_sliders = [s for s in all_sliders if s.maximum() == 30]
        assert len(interval_sliders) == 1
        assert interval_sliders[0].value() == 10
