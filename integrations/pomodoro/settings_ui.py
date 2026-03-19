"""Settings UI sections for the Pomodoro integration."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QSpinBox, QWidget

from src.ui.settings.widgets import SectionCard, make_form_row, make_slider_row


def build_settings_sections(
    pending: dict,
    font: str,
    integration_manager=None,
) -> list[QWidget]:
    """Build and return the list of settings section widgets for Pomodoro.

    Args:
        pending: Mutable settings dict that widgets write into on change.
        font: Font family string for labels and styling.
        integration_manager: Optional integration manager (unused, for API parity).

    Returns:
        A list of SectionCard widgets ready to be inserted into a tab layout.
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

    sections: list[QWidget] = []

    # -- Section 1: Durations --
    dur_section = SectionCard("Pomodoro — Durations", font)
    dur_layout = dur_section.content_layout()

    focus_row, _ = make_slider_row(
        label="Focus (min)",
        minimum=1,
        maximum=120,
        value=_get(["integrations", "pomodoro", "work_duration_minutes"], 25),
        font=font,
        on_changed=lambda v: _set(["integrations", "pomodoro", "work_duration_minutes"], v),
    )
    dur_layout.addLayout(focus_row)

    short_row, _ = make_slider_row(
        label="Short Break (min)",
        minimum=1,
        maximum=30,
        value=_get(["integrations", "pomodoro", "short_break_minutes"], 5),
        font=font,
        label_width=140,
        on_changed=lambda v: _set(["integrations", "pomodoro", "short_break_minutes"], v),
    )
    dur_layout.addLayout(short_row)

    long_row, _ = make_slider_row(
        label="Long Break (min)",
        minimum=1,
        maximum=60,
        value=_get(["integrations", "pomodoro", "long_break_minutes"], 15),
        font=font,
        label_width=140,
        on_changed=lambda v: _set(["integrations", "pomodoro", "long_break_minutes"], v),
    )
    dur_layout.addLayout(long_row)

    sections.append(dur_section)

    # -- Section 2: Cycle & Options --
    opts_section = SectionCard("Pomodoro — Cycle & Options", font)
    opts_layout = opts_section.content_layout()

    sessions_spin = QSpinBox()
    sessions_spin.setMinimum(1)
    sessions_spin.setMaximum(12)
    sessions_spin.setValue(_get(["integrations", "pomodoro", "sessions_per_cycle"], 4))
    sessions_spin.valueChanged.connect(
        lambda v: _set(["integrations", "pomodoro", "sessions_per_cycle"], v)
    )
    make_form_row("Sessions / Cycle", sessions_spin, opts_layout, font)

    auto_start_cb = QCheckBox("Auto-start next session after break")
    auto_start_cb.setChecked(_get(["integrations", "pomodoro", "auto_start"], False))
    auto_start_cb.checkStateChanged.connect(
        lambda state: _set(
            ["integrations", "pomodoro", "auto_start"],
            state == Qt.CheckState.Checked,
        )
    )
    opts_layout.addWidget(auto_start_cb)

    sound_cb = QCheckBox("Sound notifications")
    sound_cb.setChecked(_get(["integrations", "pomodoro", "sound_enabled"], True))
    sound_cb.checkStateChanged.connect(
        lambda state: _set(
            ["integrations", "pomodoro", "sound_enabled"],
            state == Qt.CheckState.Checked,
        )
    )
    opts_layout.addWidget(sound_cb)

    sections.append(opts_section)

    return sections
