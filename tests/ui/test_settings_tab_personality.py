import copy

from PyQt6.QtWidgets import QCheckBox, QLineEdit, QRadioButton, QStackedWidget, QWidget

import config
from src.ui.settings.tab_personality import build_personality_tab


def _make_pending():
    return copy.deepcopy(config.DEFAULT_SETTINGS)


class TestPersonalityTab:
    def test_creates_widget(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        assert isinstance(page, QWidget)

    def test_has_enable_checkbox(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        cb = None
        for w in page.findChildren(QCheckBox):
            if "LLM" in w.text() or "personality" in w.text().lower():
                cb = w
                break
        assert cb is not None

    def test_has_three_radio_buttons(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        radios = page.findChildren(QRadioButton)
        assert len(radios) == 3

    def test_radio_labels(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        radios = page.findChildren(QRadioButton)
        labels = sorted([r.text() for r in radios])
        assert "Ollama" in labels
        assert "OpenAI" in labels
        assert "OpenRouter" in labels

    def test_default_selects_openai(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        radios = page.findChildren(QRadioButton)
        openai_radio = [r for r in radios if "OpenAI" in r.text()][0]
        assert openai_radio.isChecked()

    def test_has_stacked_widget(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        stacked = page.findChildren(QStackedWidget)
        assert len(stacked) >= 1
        assert stacked[0].count() == 3

    def test_openai_api_key_field_exists(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        fields = [w for w in page.findChildren(QLineEdit) if w.placeholderText() == "sk-..."]
        assert len(fields) >= 1

    def test_switching_radio_changes_stacked(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        radios = page.findChildren(QRadioButton)
        stacked = page.findChildren(QStackedWidget)[0]
        ollama_radio = [r for r in radios if "Ollama" in r.text()][0]
        ollama_radio.setChecked(True)
        assert stacked.currentIndex() == 2

    def test_auto_selects_openrouter_when_key_present(self, qtbot):
        pending = _make_pending()
        pending["personality_engine"]["openrouter_api_key"] = "sk-or-test123"
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        radios = page.findChildren(QRadioButton)
        or_radio = [r for r in radios if "OpenRouter" in r.text()][0]
        assert or_radio.isChecked()

    def test_api_key_updates_pending(self, qtbot):
        pending = _make_pending()
        page = build_personality_tab(pending, font="sans-serif")
        qtbot.addWidget(page)
        fields = [w for w in page.findChildren(QLineEdit) if w.placeholderText() == "sk-..."]
        fields[0].setText("sk-test-key")
        assert pending["personality_engine"]["openai_api_key"] == "sk-test-key"
