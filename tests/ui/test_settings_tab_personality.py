"""Tests for the personality settings tab (LiteLLM provider dropdown)."""

from __future__ import annotations

import copy

from PyQt6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QWidget

import config
from src.services.personality_engine import PROVIDER_CONFIG
from src.ui.settings.tab_personality import build_personality_tab


def _make_pending():
    return copy.deepcopy(config.DEFAULT_SETTINGS)


class TestPersonalityTab:
    def test_creates_widget(self, qtbot):
        page = build_personality_tab(_make_pending(), font="sans-serif")
        qtbot.addWidget(page)
        assert isinstance(page, QWidget)

    def test_has_enable_checkbox(self, qtbot):
        page = build_personality_tab(_make_pending(), font="sans-serif")
        qtbot.addWidget(page)
        cbs = [
            w
            for w in page.findChildren(QCheckBox)
            if "LLM" in w.text() or "personality" in w.text().lower()
        ]
        assert len(cbs) >= 1

    def test_has_provider_combobox(self, qtbot):
        page = build_personality_tab(_make_pending(), font="sans-serif")
        qtbot.addWidget(page)
        combos = page.findChildren(QComboBox)
        assert len(combos) >= 1

    def test_combobox_has_all_providers(self, qtbot):
        page = build_personality_tab(_make_pending(), font="sans-serif")
        qtbot.addWidget(page)
        combo = page.findChildren(QComboBox)[0]
        items = [combo.itemData(i) for i in range(combo.count())]
        for provider_key in PROVIDER_CONFIG:
            assert provider_key in items, f"Missing provider: {provider_key}"

    def test_default_selects_openai(self, qtbot):
        page = build_personality_tab(_make_pending(), font="sans-serif")
        qtbot.addWidget(page)
        combo = page.findChildren(QComboBox)[0]
        assert combo.currentData() == "openai"

    def test_selects_saved_provider(self, qtbot):
        pending = _make_pending()
        pending["personality_engine"]["provider"] = "ollama"
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        combo = page.findChildren(QComboBox)[0]
        assert combo.currentData() == "ollama"

    def test_has_model_field(self, qtbot):
        page = build_personality_tab(_make_pending(), font="sans-serif")
        qtbot.addWidget(page)
        fields = page.findChildren(QLineEdit)
        model_fields = [f for f in fields if f.text() == "gpt-4o-mini"]
        assert len(model_fields) >= 1

    def test_cloud_provider_shows_api_key_field(self, qtbot):
        page = build_personality_tab(_make_pending(), font="sans-serif")
        qtbot.addWidget(page)
        password_fields = [
            f for f in page.findChildren(QLineEdit) if f.echoMode() == QLineEdit.EchoMode.Password
        ]
        assert len(password_fields) >= 1

    def test_provider_change_updates_pending(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        combo = page.findChildren(QComboBox)[0]
        for i in range(combo.count()):
            if combo.itemData(i) == "anthropic":
                combo.setCurrentIndex(i)
                break
        assert pending["personality_engine"]["provider"] == "anthropic"

    def test_api_key_updates_pending(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        password_fields = [
            f for f in page.findChildren(QLineEdit) if f.echoMode() == QLineEdit.EchoMode.Password
        ]
        password_fields[0].setText("sk-test-key")
        assert pending["personality_engine"]["api_key"] == "sk-test-key"

    def test_no_radio_buttons(self, qtbot):
        from PyQt6.QtWidgets import QRadioButton

        page = build_personality_tab(_make_pending(), font="sans-serif")
        qtbot.addWidget(page)
        radios = page.findChildren(QRadioButton)
        assert len(radios) == 0
