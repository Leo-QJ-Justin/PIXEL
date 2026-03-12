"""Personality settings tab with provider radio selector."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .widgets import CollapsibleSection, make_form_row, make_tab_page


def build_personality_tab(pending: dict, font: str) -> QWidget:
    """Build the Personality settings tab widget.

    Args:
        pending: Mutable settings buffer dict; changes are written directly.
        font: Font family string for styling.

    Returns:
        A QWidget suitable for placement in a QStackedWidget.
    """

    def _get(keys: list, default=None):
        d = pending
        for k in keys[:-1]:
            d = d.get(k, {})
        return d.get(keys[-1], default)

    def _set(keys: list, value) -> None:
        d = pending
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    page, outer_layout = make_tab_page(font)

    # Wrap in a scroll area so sections don't get clipped on small screens
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)

    inner = QWidget()
    layout = QVBoxLayout(inner)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)

    scroll.setWidget(inner)
    outer_layout.addWidget(scroll)

    # -----------------------------------------------------------------------
    # Section 1: Personality Engine
    # -----------------------------------------------------------------------
    engine_section = CollapsibleSection("Personality Engine", font)
    engine_layout = engine_section.content_layout()

    # Enable LLM personality enrichment checkbox
    enable_cb = QCheckBox("Enable LLM personality enrichment")
    enable_cb.setChecked(_get(["personality_engine", "enabled"], False))
    enable_cb.checkStateChanged.connect(
        lambda state: _set(
            ["personality_engine", "enabled"],
            state == Qt.CheckState.Checked,
        )
    )
    engine_layout.addWidget(enable_cb)

    # Note text label
    note_lbl = QLabel(
        "When enabled, bubble text is rewritten in Haro's voice using an LLM. "
        "Bypassed when OpenClaw is running."
    )
    note_lbl.setWordWrap(True)
    note_lbl.setStyleSheet(
        f"color: {theme.COLORS['text_muted']}; font-family: '{font}'; font-size: 12px;"
    )
    engine_layout.addWidget(note_lbl)

    layout.addWidget(engine_section)

    # -----------------------------------------------------------------------
    # Section 2: Provider
    # -----------------------------------------------------------------------
    provider_section = CollapsibleSection("Provider", font)
    provider_layout = provider_section.content_layout()

    # Radio buttons row
    radio_row = QHBoxLayout()
    radio_row.setSpacing(16)

    radio_openai = QRadioButton("OpenAI")
    radio_openrouter = QRadioButton("OpenRouter")
    radio_ollama = QRadioButton("Ollama")

    radio_row.addWidget(radio_openai)
    radio_row.addWidget(radio_openrouter)
    radio_row.addWidget(radio_ollama)
    radio_row.addStretch()

    provider_layout.addLayout(radio_row)

    # Stacked widget with one page per provider
    stacked = QStackedWidget()

    # --- Page 0: OpenAI ---
    openai_page = QWidget()
    openai_layout = QVBoxLayout(openai_page)
    openai_layout.setContentsMargins(0, 8, 0, 0)
    openai_layout.setSpacing(8)

    openai_key = QLineEdit()
    openai_key.setEchoMode(QLineEdit.EchoMode.Password)
    openai_key.setPlaceholderText("sk-...")
    openai_key.setText(_get(["personality_engine", "openai_api_key"], ""))
    openai_key.textChanged.connect(lambda v: _set(["personality_engine", "openai_api_key"], v))
    make_form_row("API Key", openai_key, openai_layout, font)

    openai_model = QLineEdit()
    openai_model.setText(_get(["personality_engine", "openai_model"], "gpt-4o-mini"))
    openai_model.textChanged.connect(lambda v: _set(["personality_engine", "openai_model"], v))
    make_form_row("Model", openai_model, openai_layout, font)

    openai_layout.addStretch()
    stacked.addWidget(openai_page)

    # --- Page 1: OpenRouter ---
    openrouter_page = QWidget()
    openrouter_layout = QVBoxLayout(openrouter_page)
    openrouter_layout.setContentsMargins(0, 8, 0, 0)
    openrouter_layout.setSpacing(8)

    openrouter_key = QLineEdit()
    openrouter_key.setEchoMode(QLineEdit.EchoMode.Password)
    openrouter_key.setPlaceholderText("sk-or-...")
    openrouter_key.setText(_get(["personality_engine", "openrouter_api_key"], ""))
    openrouter_key.textChanged.connect(
        lambda v: _set(["personality_engine", "openrouter_api_key"], v)
    )
    make_form_row("API Key", openrouter_key, openrouter_layout, font)

    openrouter_model = QLineEdit()
    openrouter_model.setText(
        _get(
            ["personality_engine", "openrouter_model"],
            "meta-llama/llama-3-8b-instruct",
        )
    )
    openrouter_model.textChanged.connect(
        lambda v: _set(["personality_engine", "openrouter_model"], v)
    )
    make_form_row("Model", openrouter_model, openrouter_layout, font)

    openrouter_layout.addStretch()
    stacked.addWidget(openrouter_page)

    # --- Page 2: Ollama ---
    ollama_page = QWidget()
    ollama_layout = QVBoxLayout(ollama_page)
    ollama_layout.setContentsMargins(0, 8, 0, 0)
    ollama_layout.setSpacing(8)

    ollama_endpoint = QLineEdit()
    ollama_endpoint.setText(
        _get(["personality_engine", "ollama_endpoint"], "http://localhost:11434")
    )
    ollama_endpoint.textChanged.connect(
        lambda v: _set(["personality_engine", "ollama_endpoint"], v)
    )
    make_form_row("Endpoint", ollama_endpoint, ollama_layout, font)

    ollama_model = QLineEdit()
    ollama_model.setText(_get(["personality_engine", "ollama_model"], "llama3"))
    ollama_model.textChanged.connect(lambda v: _set(["personality_engine", "ollama_model"], v))
    make_form_row("Model", ollama_model, ollama_layout, font)

    ollama_layout.addStretch()
    stacked.addWidget(ollama_page)

    provider_layout.addWidget(stacked)

    # Auto-select logic: determine which radio to check based on current settings
    openrouter_key_val = _get(["personality_engine", "openrouter_api_key"], "")
    openai_key_val = _get(["personality_engine", "openai_api_key"], "")
    ollama_endpoint_val = _get(["personality_engine", "ollama_endpoint"], "http://localhost:11434")
    _ollama_default = "http://localhost:11434"

    if openrouter_key_val:
        radio_openrouter.setChecked(True)
        stacked.setCurrentIndex(1)
    elif ollama_endpoint_val != _ollama_default and not openai_key_val:
        radio_ollama.setChecked(True)
        stacked.setCurrentIndex(2)
    else:
        radio_openai.setChecked(True)
        stacked.setCurrentIndex(0)

    # Connect radio buttons to stacked widget
    radio_openai.toggled.connect(lambda checked: stacked.setCurrentIndex(0) if checked else None)
    radio_openrouter.toggled.connect(
        lambda checked: stacked.setCurrentIndex(1) if checked else None
    )
    radio_ollama.toggled.connect(lambda checked: stacked.setCurrentIndex(2) if checked else None)

    layout.addWidget(provider_section)
    layout.addStretch()

    return page
