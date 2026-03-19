"""Personality settings tab with LiteLLM provider dropdown."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.services.personality_engine import PROVIDER_CONFIG

from . import theme
from .widgets import CollapsibleSection, make_form_row, make_tab_page

# Display name → provider key pairs in a friendly order
_PROVIDER_DISPLAY: list[tuple[str, str]] = [
    ("OpenAI", "openai"),
    ("Anthropic", "anthropic"),
    ("OpenRouter", "openrouter"),
    ("Groq", "groq"),
    ("Mistral", "mistral"),
    ("Google Gemini", "google_gemini"),
    ("Together AI", "together_ai"),
    ("DeepSeek", "deepseek"),
    ("Ollama (local)", "ollama"),
    ("Custom / OpenAI-compatible", "custom"),
]


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

    # Provider dropdown
    provider_combo = QComboBox()
    for display_name, key in _PROVIDER_DISPLAY:
        provider_combo.addItem(display_name, userData=key)

    make_form_row("Provider", provider_combo, provider_layout, font)

    # --- API Key field (shown for cloud providers) ---
    api_key_row_container = QWidget()
    api_key_row_layout = QVBoxLayout(api_key_row_container)
    api_key_row_layout.setContentsMargins(0, 0, 0, 0)
    api_key_row_layout.setSpacing(0)

    api_key_field = QLineEdit()
    api_key_field.setEchoMode(QLineEdit.EchoMode.Password)
    api_key_field.setPlaceholderText("sk-...")
    api_key_field.setText(_get(["personality_engine", "api_key"], ""))
    api_key_field.textChanged.connect(lambda v: _set(["personality_engine", "api_key"], v))
    make_form_row("API Key", api_key_field, api_key_row_layout, font)

    provider_layout.addWidget(api_key_row_container)

    # --- Endpoint field (shown for Ollama / custom) ---
    endpoint_row_container = QWidget()
    endpoint_row_layout = QVBoxLayout(endpoint_row_container)
    endpoint_row_layout.setContentsMargins(0, 0, 0, 0)
    endpoint_row_layout.setSpacing(0)

    endpoint_field = QLineEdit()
    endpoint_field.setPlaceholderText("http://localhost:11434")
    endpoint_field.setText(_get(["personality_engine", "endpoint"], ""))
    endpoint_field.textChanged.connect(lambda v: _set(["personality_engine", "endpoint"], v))
    make_form_row("Endpoint", endpoint_field, endpoint_row_layout, font)

    provider_layout.addWidget(endpoint_row_container)

    # --- Model field (always shown) ---
    model_field = QLineEdit()
    model_field.setText(_get(["personality_engine", "model"], "gpt-4o-mini"))
    model_field.textChanged.connect(lambda v: _set(["personality_engine", "model"], v))
    make_form_row("Model", model_field, provider_layout, font)

    # -----------------------------------------------------------------------
    # Dynamic visibility callback
    # -----------------------------------------------------------------------

    def _on_provider_changed(index: int) -> None:
        key = provider_combo.itemData(index)
        cfg = PROVIDER_CONFIG.get(key, {})

        # Update pending provider
        _set(["personality_engine", "provider"], key)

        # Show/hide api_key and endpoint rows based on provider needs
        api_key_row_container.setVisible(bool(cfg.get("needs_api_key", False)))
        endpoint_row_container.setVisible(bool(cfg.get("needs_endpoint", False)))

        # Auto-fill model if current value is empty or matches the previous provider's default
        current_model = model_field.text().strip()
        provider_default = cfg.get("default_model", "")

        # Check if the current model text matches any known provider default
        is_default_model = any(
            current_model == pc.get("default_model", "") for pc in PROVIDER_CONFIG.values()
        )

        if not current_model or is_default_model:
            model_field.setText(provider_default)

    provider_combo.currentIndexChanged.connect(_on_provider_changed)

    # Select the saved provider
    saved_provider = _get(["personality_engine", "provider"], "openai")
    for i in range(provider_combo.count()):
        if provider_combo.itemData(i) == saved_provider:
            provider_combo.setCurrentIndex(i)
            break

    # Explicitly call _on_provider_changed to set correct initial visibility
    # (needed when the saved provider is index 0 and currentIndexChanged isn't emitted)
    _on_provider_changed(provider_combo.currentIndex())

    layout.addWidget(provider_section)
    layout.addStretch()

    return page
