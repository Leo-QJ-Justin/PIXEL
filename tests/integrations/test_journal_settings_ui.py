"""Tests for journal settings UI builder."""

import copy

from PyQt6.QtWidgets import QCheckBox, QComboBox, QWidget

import config


def _make_pending():
    pending = copy.deepcopy(config.DEFAULT_SETTINGS)
    pending.setdefault("integrations", {}).setdefault(
        "journal",
        {
            "nudge_frequency": "smart",
            "nudge_time": "20:00",
            "blur_on_focus_loss": True,
        },
    )
    return pending


class TestJournalSettingsUI:
    def test_returns_list_of_widgets(self, qtbot):
        from integrations.journal.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        assert isinstance(sections, list)
        assert len(sections) >= 1
        for s in sections:
            assert isinstance(s, QWidget)

    def test_has_nudge_frequency_combo(self, qtbot):
        from integrations.journal.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        all_combos = []
        for s in sections:
            qtbot.addWidget(s)
            all_combos.extend(s.findChildren(QComboBox))
        assert len(all_combos) >= 1
        freq_combo = all_combos[0]
        items = [freq_combo.itemText(i) for i in range(freq_combo.count())]
        assert "never" in items
        assert "smart" in items
        assert "once_daily" in items

    def test_nudge_frequency_updates_pending(self, qtbot):
        from integrations.journal.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        for s in sections:
            qtbot.addWidget(s)
        combos = []
        for s in sections:
            combos.extend(s.findChildren(QComboBox))
        combos[0].setCurrentText("never")
        assert pending["integrations"]["journal"]["nudge_frequency"] == "never"

    def test_has_blur_checkbox(self, qtbot):
        from integrations.journal.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        all_checks = []
        for s in sections:
            qtbot.addWidget(s)
            all_checks.extend(s.findChildren(QCheckBox))
        assert len(all_checks) >= 1

    def test_blur_updates_pending(self, qtbot):
        from integrations.journal.settings_ui import build_settings_sections

        pending = _make_pending()
        sections = build_settings_sections(pending, font="sans-serif")
        for s in sections:
            qtbot.addWidget(s)
        checks = []
        for s in sections:
            checks.extend(s.findChildren(QCheckBox))
        checks[0].setChecked(False)
        assert pending["integrations"]["journal"]["blur_on_focus_loss"] is False
