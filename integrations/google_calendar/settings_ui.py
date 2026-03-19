"""Settings UI sections for the Google Calendar integration."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QPushButton, QWidget

from integrations.google_calendar.auth import is_authenticated
from src.ui.settings import theme
from src.ui.settings.widgets import SectionCard, make_slider_row


def build_settings_sections(
    pending: dict,
    font: str,
    integration_manager=None,
) -> list[QWidget]:
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

    sections: list[QWidget] = []

    # -- Section 1: Account --
    account_section = SectionCard("Google Calendar — Account", font)
    account_layout = account_section.content_layout()

    connected = is_authenticated(BASE_DIR)

    status_label = QLabel("Connected" if connected else "Not connected")
    status_label.setStyleSheet(
        f"color: {theme.COLORS['success'] if connected else theme.COLORS['text_muted']}; "
        f"font-family: '{font}'; font-size: 13px;"
    )
    account_layout.addWidget(status_label)

    connect_btn = QPushButton("Connect Google Calendar")
    connect_btn.setVisible(not connected)

    disconnect_btn = QPushButton("Disconnect")
    disconnect_btn.setVisible(connected)

    def _on_connect():
        import asyncio
        from threading import Thread

        from integrations.google_calendar.auth import run_auth_flow

        connect_btn.setEnabled(False)
        status_label.setText("Connecting...")

        def _run_flow():
            return run_auth_flow(BASE_DIR)

        def _on_done(creds):
            connect_btn.setEnabled(True)
            if creds is None:
                status_label.setText("Connection failed")
                status_label.setStyleSheet(
                    f"color: {theme.COLORS['destructive']}; font-family: '{font}'; font-size: 13px;"
                )
                return
            status_label.setText("Connected")
            status_label.setStyleSheet(
                f"color: {theme.COLORS['success']}; font-family: '{font}'; font-size: 13px;"
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

        def _thread_target():
            creds = _run_flow()
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(0, lambda: _on_done(creds))

        Thread(target=_thread_target, daemon=True).start()

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
            f"color: {theme.COLORS['text_muted']}; font-family: '{font}'; font-size: 13px;"
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
    account_layout.addLayout(btn_row)

    sections.append(account_section)

    # -- Section 2: Reminders --
    reminders_section = SectionCard("Google Calendar — Reminders", font)
    reminders_layout = reminders_section.content_layout()

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
        reminders_layout.addWidget(cb)

    sections.append(reminders_section)

    # -- Section 3: Options --
    opts_section = SectionCard("Google Calendar — Options", font)
    opts_layout = opts_section.content_layout()

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
    opts_layout.addWidget(day_preview_cb)

    current_ms = _get(["integrations", "google_calendar", "check_interval_ms"], 300000)
    current_min = max(1, min(15, current_ms // 60000))

    check_row, _ = make_slider_row(
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
    opts_layout.addLayout(check_row)

    sections.append(opts_section)

    return sections
