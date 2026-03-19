"""Settings UI sections for the Weather integration."""

from __future__ import annotations

from PyQt6.QtWidgets import QComboBox, QLineEdit, QWidget

from src.ui.settings.widgets import SectionCard, make_form_row, make_slider_row

_UNITS_OPTIONS = [
    ("Metric (\u00b0C)", "metric"),
    ("Imperial (\u00b0F)", "imperial"),
]


def build_settings_sections(
    pending: dict,
    font: str,
    integration_manager=None,
) -> list[QWidget]:
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

    section = SectionCard("Weather", font)
    layout = section.content_layout()

    # City input
    city_edit = QLineEdit()
    city_edit.setText(_get(["integrations", "weather", "city"], "New York"))
    city_edit.setPlaceholderText("Enter city name...")
    city_edit.textChanged.connect(lambda text: _set(["integrations", "weather", "city"], text))
    make_form_row("City", city_edit, layout, font)

    # Units combobox
    units_combo = QComboBox()
    current_units = _get(["integrations", "weather", "units"], "metric")
    for display_text, value in _UNITS_OPTIONS:
        units_combo.addItem(display_text, value)
    for i, (_, value) in enumerate(_UNITS_OPTIONS):
        if value == current_units:
            units_combo.setCurrentIndex(i)
            break
    units_combo.currentIndexChanged.connect(
        lambda idx: _set(
            ["integrations", "weather", "units"],
            units_combo.itemData(idx),
        )
    )
    make_form_row("Units", units_combo, layout, font)

    # Check interval slider (1-30 min)
    current_ms = _get(["integrations", "weather", "check_interval_ms"], 600000)
    current_min = max(1, min(30, current_ms // 60000))

    check_row, _ = make_slider_row(
        label="Check every",
        minimum=1,
        maximum=30,
        value=current_min,
        font=font,
        suffix=" min",
        on_changed=lambda v: _set(["integrations", "weather", "check_interval_ms"], v * 60000),
    )
    layout.addLayout(check_row)

    return [section]
