"""Behaviors tab for the settings dialog.

Merges the old Behaviors tab and Encouraging tab into a single page
with CollapsibleSection groups.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QWidget

from . import theme
from .widgets import CollapsibleSection, make_form_row, make_slider_row, make_tab_page


def build_behaviors_tab(pending: dict, font: str) -> QWidget:
    """Build and return the Behaviors settings tab widget.

    Args:
        pending: Mutable settings dict; modified in-place as controls change.
        font: Font family string for labels and controls.

    Returns:
        A QWidget representing the full tab page.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Page scaffold
    # ------------------------------------------------------------------

    page, layout = make_tab_page(font)

    # ------------------------------------------------------------------
    # Section 1: Fly / Wander
    # ------------------------------------------------------------------

    wander_sec = CollapsibleSection("Fly / Wander", font)
    cl = wander_sec.content_layout()

    # Wander Chance slider (0-100 → stored as 0.0-1.0)
    wander_chance_row, _ = make_slider_row(
        label="Wander Chance",
        minimum=0,
        maximum=100,
        value=int(_get(["behaviors", "wander", "wander_chance"], 0.3) * 100),
        font=font,
        suffix="%",
        on_changed=lambda v: _set(["behaviors", "wander", "wander_chance"], v / 100.0),
    )
    cl.addLayout(wander_chance_row)

    # Interval (ms) — label + min spinbox + "to" + max spinbox
    interval_row = QHBoxLayout()
    interval_row.setSpacing(12)

    interval_lbl = QLabel("Interval (ms)")
    interval_lbl.setFixedWidth(120)
    interval_lbl.setStyleSheet(
        f"color: {theme.COLORS['text_muted']}; font-family: '{font}'; font-size: 13px;"
    )

    spin_min = QSpinBox()
    spin_min.setMinimum(1000)
    spin_min.setMaximum(60000)
    spin_min.setSingleStep(1000)
    spin_min.setValue(_get(["behaviors", "wander", "wander_interval_min_ms"], 5000))
    spin_min.valueChanged.connect(
        lambda v: _set(["behaviors", "wander", "wander_interval_min_ms"], v)
    )

    to_lbl = QLabel("to")
    to_lbl.setFixedWidth(20)
    to_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    to_lbl.setStyleSheet(
        f"color: {theme.COLORS['text_muted']}; font-family: '{font}'; font-size: 13px;"
    )

    spin_max = QSpinBox()
    spin_max.setMinimum(1000)
    spin_max.setMaximum(60000)
    spin_max.setSingleStep(1000)
    spin_max.setValue(_get(["behaviors", "wander", "wander_interval_max_ms"], 15000))
    spin_max.valueChanged.connect(
        lambda v: _set(["behaviors", "wander", "wander_interval_max_ms"], v)
    )

    interval_row.addWidget(interval_lbl)
    interval_row.addWidget(spin_min, stretch=1)
    interval_row.addWidget(to_lbl)
    interval_row.addWidget(spin_max, stretch=1)

    cl.addLayout(interval_row)

    layout.addWidget(wander_sec)

    # ------------------------------------------------------------------
    # Section 2: Wave
    # ------------------------------------------------------------------

    wave_sec = CollapsibleSection("Wave", font)
    wl = wave_sec.content_layout()

    greeting_edit = QLineEdit()
    greeting_edit.setText(_get(["behaviors", "wave", "greeting"], "Hello!"))
    greeting_edit.textChanged.connect(lambda v: _set(["behaviors", "wave", "greeting"], v))
    make_form_row("Greeting", greeting_edit, wl, font)

    layout.addWidget(wave_sec)

    # ------------------------------------------------------------------
    # Section 3: Encouraging Messages
    # ------------------------------------------------------------------

    enc_sec = CollapsibleSection("Encouraging Messages", font)
    el = enc_sec.content_layout()

    enable_cb = QCheckBox("Enable Encouraging Messages")
    enable_cb.setChecked(_get(["integrations", "encouraging", "enabled"], True))
    enable_cb.checkStateChanged.connect(
        lambda state: _set(
            ["integrations", "encouraging", "enabled"],
            state == Qt.CheckState.Checked,
        )
    )
    el.addWidget(enable_cb)

    cooldown_row, _ = make_slider_row(
        label="Min Cooldown",
        minimum=15,
        maximum=120,
        value=_get(["integrations", "encouraging", "cooldown_min_minutes"], 30),
        font=font,
        suffix=" min",
        on_changed=lambda v: _set(["integrations", "encouraging", "cooldown_min_minutes"], v),
    )
    el.addLayout(cooldown_row)

    layout.addWidget(enc_sec)

    # ------------------------------------------------------------------
    # Section 4: Encouraging Triggers
    # ------------------------------------------------------------------

    trig_sec = CollapsibleSection("Encouraging Triggers", font)
    tl = trig_sec.content_layout()

    trigger_labels = [
        ("restless", "Restless (long activity)"),
        ("observant", "Observant (time of day)"),
        ("excited", "Excited (return from idle)"),
        ("proud", "Proud (pomodoro streak)"),
        ("curious", "Curious (meeting ended)"),
        ("impressed", "Impressed (session milestones)"),
    ]

    for key, label in trigger_labels:
        cb = QCheckBox(label)
        cb.setChecked(_get(["integrations", "encouraging", "triggers", key, "enabled"], True))
        # Capture key in default arg to avoid late-binding closure issue
        cb.checkStateChanged.connect(
            lambda state, k=key: _set(
                ["integrations", "encouraging", "triggers", k, "enabled"],
                state == Qt.CheckState.Checked,
            )
        )
        tl.addWidget(cb)

    # Restless Threshold slider
    restless_row, _ = make_slider_row(
        label="Restless Threshold",
        minimum=30,
        maximum=180,
        value=_get(
            ["integrations", "encouraging", "triggers", "restless", "threshold_minutes"],
            90,
        ),
        font=font,
        suffix=" min",
        on_changed=lambda v: _set(
            ["integrations", "encouraging", "triggers", "restless", "threshold_minutes"],
            v,
        ),
    )
    tl.addLayout(restless_row)

    layout.addWidget(trig_sec)

    layout.addStretch()

    return page
