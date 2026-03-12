"""Integrations settings tab (merges Pomodoro + Google Calendar)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

# Module-level import so tests can patch it
from integrations.google_calendar.auth import is_authenticated

from . import theme
from .widgets import CollapsibleSection, make_form_row, make_slider_row, make_tab_page


def build_integrations_tab(pending: dict, font: str, integration_manager=None) -> QWidget:
    """Build the Integrations settings tab widget (Pomodoro + Google Calendar).

    Args:
        pending: Mutable settings buffer dict; changes are written directly.
        font: Font family string for styling.
        integration_manager: Optional integration manager for start/stop calls.

    Returns:
        A QWidget suitable for placement in a QStackedWidget.
    """
    from config import BASE_DIR

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
    # Section 1: Pomodoro — Durations
    # -----------------------------------------------------------------------
    pomo_dur_section = CollapsibleSection("Pomodoro — Durations", font)
    pomo_dur_layout = pomo_dur_section.content_layout()

    # Focus slider (1-120 min)
    focus_row, _get_focus = make_slider_row(
        label="Focus (min)",
        minimum=1,
        maximum=120,
        value=_get(["integrations", "pomodoro", "work_duration_minutes"], 25),
        font=font,
        on_changed=lambda v: _set(["integrations", "pomodoro", "work_duration_minutes"], v),
    )
    pomo_dur_layout.addLayout(focus_row)

    # Short Break slider (1-30 min)
    short_break_row, _get_short_break = make_slider_row(
        label="Short Break (min)",
        minimum=1,
        maximum=30,
        value=_get(["integrations", "pomodoro", "short_break_minutes"], 5),
        font=font,
        label_width=140,
        on_changed=lambda v: _set(["integrations", "pomodoro", "short_break_minutes"], v),
    )
    pomo_dur_layout.addLayout(short_break_row)

    # Long Break slider (1-60 min)
    long_break_row, _get_long_break = make_slider_row(
        label="Long Break (min)",
        minimum=1,
        maximum=60,
        value=_get(["integrations", "pomodoro", "long_break_minutes"], 15),
        font=font,
        label_width=140,
        on_changed=lambda v: _set(["integrations", "pomodoro", "long_break_minutes"], v),
    )
    pomo_dur_layout.addLayout(long_break_row)

    layout.addWidget(pomo_dur_section)

    # -----------------------------------------------------------------------
    # Section 2: Pomodoro — Cycle & Options
    # -----------------------------------------------------------------------
    pomo_opts_section = CollapsibleSection("Pomodoro — Cycle & Options", font)
    pomo_opts_layout = pomo_opts_section.content_layout()

    # Sessions per cycle (QSpinBox 1-12)
    sessions_spin = QSpinBox()
    sessions_spin.setMinimum(1)
    sessions_spin.setMaximum(12)
    sessions_spin.setValue(_get(["integrations", "pomodoro", "sessions_per_cycle"], 4))
    sessions_spin.valueChanged.connect(
        lambda v: _set(["integrations", "pomodoro", "sessions_per_cycle"], v)
    )
    make_form_row("Sessions / Cycle", sessions_spin, pomo_opts_layout, font)

    # Auto-start checkbox
    auto_start_cb = QCheckBox("Auto-start next session after break")
    auto_start_cb.setChecked(_get(["integrations", "pomodoro", "auto_start"], False))
    auto_start_cb.checkStateChanged.connect(
        lambda state: _set(
            ["integrations", "pomodoro", "auto_start"],
            state == Qt.CheckState.Checked,
        )
    )
    pomo_opts_layout.addWidget(auto_start_cb)

    # Sound notifications checkbox
    sound_cb = QCheckBox("Sound notifications")
    sound_cb.setChecked(_get(["integrations", "pomodoro", "sound_enabled"], True))
    sound_cb.checkStateChanged.connect(
        lambda state: _set(
            ["integrations", "pomodoro", "sound_enabled"],
            state == Qt.CheckState.Checked,
        )
    )
    pomo_opts_layout.addWidget(sound_cb)

    layout.addWidget(pomo_opts_section)

    # -----------------------------------------------------------------------
    # Section 3: Google Calendar — Account
    # -----------------------------------------------------------------------
    gcal_account_section = CollapsibleSection("Google Calendar — Account", font)
    gcal_account_layout = gcal_account_section.content_layout()

    connected = is_authenticated(BASE_DIR)

    # Status label
    status_label = QLabel("Connected" if connected else "Not connected")
    status_label.setStyleSheet(
        f"color: {theme.COLORS['success'] if connected else theme.COLORS['text_muted']}; "
        f"font-family: '{font}'; font-size: 13px;"
    )
    gcal_account_layout.addWidget(status_label)

    # Connect button (visible when NOT connected)
    connect_btn = QPushButton("Connect Google Calendar")
    connect_btn.setVisible(not connected)

    # Disconnect button (visible when connected)
    disconnect_btn = QPushButton("Disconnect")
    disconnect_btn.setVisible(connected)

    def _on_connect():
        import asyncio

        from integrations.google_calendar.auth import run_auth_flow

        creds = run_auth_flow(BASE_DIR)
        if creds is None:
            status_label.setText("Connection failed")
            status_label.setStyleSheet(
                f"color: {theme.COLORS['destructive']}; " f"font-family: '{font}'; font-size: 13px;"
            )
            return
        status_label.setText("Connected")
        status_label.setStyleSheet(
            f"color: {theme.COLORS['success']}; " f"font-family: '{font}'; font-size: 13px;"
        )
        connect_btn.setVisible(False)
        disconnect_btn.setVisible(True)
        _set(["integrations", "google_calendar", "enabled"], True)
        if integration_manager:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(integration_manager.start("google_calendar"))
            except RuntimeError:
                pass

    def _on_disconnect():
        import asyncio

        from integrations.google_calendar.auth import clear_credentials

        if integration_manager:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(integration_manager.stop("google_calendar"))
            except RuntimeError:
                pass
        clear_credentials(BASE_DIR)
        status_label.setText("Not connected")
        status_label.setStyleSheet(
            f"color: {theme.COLORS['text_muted']}; " f"font-family: '{font}'; font-size: 13px;"
        )
        connect_btn.setVisible(True)
        disconnect_btn.setVisible(False)
        _set(["integrations", "google_calendar", "enabled"], False)

    connect_btn.clicked.connect(_on_connect)
    disconnect_btn.clicked.connect(_on_disconnect)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(8)
    btn_row.addWidget(connect_btn)
    btn_row.addWidget(disconnect_btn)
    btn_row.addStretch()
    gcal_account_layout.addLayout(btn_row)

    layout.addWidget(gcal_account_section)

    # -----------------------------------------------------------------------
    # Section 4: Google Calendar — Reminders
    # -----------------------------------------------------------------------
    gcal_reminders_section = CollapsibleSection("Google Calendar — Reminders", font)
    gcal_reminders_layout = gcal_reminders_section.content_layout()

    reminder_options = [
        ("30 minutes before", 30),
        ("5 minutes before", 5),
        ("At event start", 0),
    ]

    for label_text, minutes in reminder_options:
        cb = QCheckBox(label_text)
        current_reminders = _get(
            ["integrations", "google_calendar", "reminder_minutes"], [30, 5, 0]
        )
        cb.setChecked(minutes in current_reminders)

        def _on_reminder_toggle(checked, m=minutes):
            reminders = _get(["integrations", "google_calendar", "reminder_minutes"], [30, 5, 0])
            if checked and m not in reminders:
                reminders.append(m)
                reminders.sort(reverse=True)
            elif not checked and m in reminders:
                reminders.remove(m)
            _set(["integrations", "google_calendar", "reminder_minutes"], reminders)

        cb.checkStateChanged.connect(
            lambda state, fn=_on_reminder_toggle: fn(state == Qt.CheckState.Checked)
        )
        gcal_reminders_layout.addWidget(cb)

    layout.addWidget(gcal_reminders_section)

    # -----------------------------------------------------------------------
    # Section 5: Google Calendar — Options
    # -----------------------------------------------------------------------
    gcal_opts_section = CollapsibleSection("Google Calendar — Options", font)
    gcal_opts_layout = gcal_opts_section.content_layout()

    # Show daily summary on startup
    day_preview_cb = QCheckBox("Show daily summary on startup")
    day_preview_cb.setChecked(
        _get(["integrations", "google_calendar", "day_preview_enabled"], True)
    )
    day_preview_cb.checkStateChanged.connect(
        lambda state: _set(
            ["integrations", "google_calendar", "day_preview_enabled"],
            state == Qt.CheckState.Checked,
        )
    )
    gcal_opts_layout.addWidget(day_preview_cb)

    # Check interval slider (1-15 min), stored as ms
    current_ms = _get(["integrations", "google_calendar", "check_interval_ms"], 300000)
    current_min = max(1, min(15, current_ms // 60000))

    check_interval_row, _get_interval = make_slider_row(
        label="Check every",
        minimum=1,
        maximum=15,
        value=current_min,
        font=font,
        suffix=" min",
        on_changed=lambda v: _set(
            ["integrations", "google_calendar", "check_interval_ms"], v * 60000
        ),
    )
    gcal_opts_layout.addLayout(check_interval_row)

    layout.addWidget(gcal_opts_section)
    layout.addStretch()

    return page
