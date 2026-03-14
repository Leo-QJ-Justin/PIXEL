"""Journal integration settings UI."""

from __future__ import annotations

from PyQt6.QtCore import QTime
from PyQt6.QtWidgets import QCheckBox, QComboBox, QTimeEdit, QWidget

from src.ui.settings.widgets import SectionCard, make_form_row


def build_settings_sections(
    pending: dict,
    font: str,
    integration_manager=None,
) -> list[QWidget]:
    """Build journal settings sections for the integrations tab."""

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

    section = SectionCard("Journal", font)
    layout = section.content_layout()

    # Nudge frequency
    freq_combo = QComboBox()
    freq_combo.addItems(["never", "once_daily", "smart"])
    current_freq = _get(["integrations", "journal", "nudge_frequency"], "smart")
    freq_combo.setCurrentText(current_freq)
    freq_combo.currentTextChanged.connect(
        lambda v: _set(["integrations", "journal", "nudge_frequency"], v)
    )
    make_form_row("Nudge frequency", freq_combo, layout, font)

    # Nudge time
    time_edit = QTimeEdit()
    nudge_time = _get(["integrations", "journal", "nudge_time"], "20:00")
    try:
        h, m = map(int, nudge_time.split(":"))
        time_edit.setTime(QTime(h, m))
    except (ValueError, AttributeError):
        time_edit.setTime(QTime(20, 0))
    time_edit.timeChanged.connect(
        lambda t: _set(["integrations", "journal", "nudge_time"], t.toString("HH:mm"))
    )
    make_form_row("Nudge time", time_edit, layout, font)

    # Blur on focus loss
    blur_check = QCheckBox("Blur journal when window loses focus")
    blur_check.setChecked(_get(["integrations", "journal", "blur_on_focus_loss"], True))
    blur_check.toggled.connect(lambda v: _set(["integrations", "journal", "blur_on_focus_loss"], v))
    layout.addWidget(blur_check)

    return [section]
