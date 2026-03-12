"""General settings tab (merges General + Time / Schedule)."""

from __future__ import annotations

from PyQt6.QtCore import QDate, Qt, QTime
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from .widgets import CollapsibleSection, make_form_row, make_slider_row, make_tab_page


def build_general_tab(pending: dict, font: str) -> QWidget:
    """Build the General settings tab widget.

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
    # Section 1: Profile
    # -----------------------------------------------------------------------
    profile_section = CollapsibleSection("Profile", font)
    profile_layout = profile_section.content_layout()

    # User Name
    name_edit = QLineEdit()
    name_edit.setPlaceholderText("Enter username...")
    name_edit.setText(_get(["user_name"], ""))
    name_edit.textChanged.connect(lambda v: _set(["user_name"], v))
    make_form_row("User Name", name_edit, profile_layout, font)

    # Birthday
    birthday_edit = QDateEdit()
    birthday_edit.setDisplayFormat("MM-dd")
    birthday_edit.setCalendarPopup(True)
    birthday_str = _get(["birthday"], "")
    if birthday_str:
        try:
            month, day = birthday_str.split("-")
            birthday_edit.setDate(QDate(2000, int(month), int(day)))
        except (ValueError, AttributeError):
            birthday_edit.setDate(QDate.currentDate())
    else:
        birthday_edit.setDate(QDate.currentDate())

    def _on_birthday_changed(date: QDate) -> None:
        _set(["birthday"], f"{date.month():02d}-{date.day():02d}")

    birthday_edit.dateChanged.connect(_on_birthday_changed)
    make_form_row("Birthday", birthday_edit, profile_layout, font)

    layout.addWidget(profile_section)

    # -----------------------------------------------------------------------
    # Section 2: Window
    # -----------------------------------------------------------------------
    window_section = CollapsibleSection("Window", font)
    window_layout = window_section.content_layout()

    # Always on top
    always_on_top_cb = QCheckBox("Always on top")
    always_on_top_cb.setChecked(_get(["general", "always_on_top"], True))
    always_on_top_cb.checkStateChanged.connect(
        lambda state: _set(
            ["general", "always_on_top"],
            state == Qt.CheckState.Checked,
        )
    )
    window_layout.addWidget(always_on_top_cb)

    # Start minimized
    start_minimized_cb = QCheckBox("Start minimized")
    start_minimized_cb.setChecked(_get(["general", "start_minimized"], False))
    start_minimized_cb.checkStateChanged.connect(
        lambda state: _set(
            ["general", "start_minimized"],
            state == Qt.CheckState.Checked,
        )
    )
    window_layout.addWidget(start_minimized_cb)

    # Start on boot
    start_on_boot_cb = QCheckBox("Start on boot")
    start_on_boot_cb.setChecked(_get(["general", "start_on_boot"], False))
    start_on_boot_cb.checkStateChanged.connect(
        lambda state: _set(
            ["general", "start_on_boot"],
            state == Qt.CheckState.Checked,
        )
    )
    window_layout.addWidget(start_on_boot_cb)

    # Default Facing
    facing_combo = QComboBox()
    facing_combo.addItem("Right", "right")
    facing_combo.addItem("Left", "left")
    current_facing = _get(["general", "sprite_default_facing"], "right")
    index = facing_combo.findData(current_facing)
    if index >= 0:
        facing_combo.setCurrentIndex(index)
    facing_combo.currentIndexChanged.connect(
        lambda _: _set(["general", "sprite_default_facing"], facing_combo.currentData())
    )
    make_form_row("Default Facing", facing_combo, window_layout, font)

    layout.addWidget(window_section)

    # -----------------------------------------------------------------------
    # Section 3: Speech Bubble
    # -----------------------------------------------------------------------
    speech_section = CollapsibleSection("Speech Bubble", font)
    speech_layout = speech_section.content_layout()

    # Enabled
    speech_enabled_cb = QCheckBox("Enabled")
    speech_enabled_cb.setChecked(_get(["general", "speech_bubble", "enabled"], True))
    speech_enabled_cb.checkStateChanged.connect(
        lambda state: _set(
            ["general", "speech_bubble", "enabled"],
            state == Qt.CheckState.Checked,
        )
    )
    speech_layout.addWidget(speech_enabled_cb)

    # Duration slider
    duration_row, _get_duration = make_slider_row(
        label="Duration",
        minimum=0,
        maximum=10000,
        value=_get(["general", "speech_bubble", "duration_ms"], 3000),
        font=font,
        suffix=" ms",
        on_changed=lambda v: _set(["general", "speech_bubble", "duration_ms"], v),
    )
    speech_layout.addLayout(duration_row)

    layout.addWidget(speech_section)

    # -----------------------------------------------------------------------
    # Section 4: Sleep & Schedule
    # -----------------------------------------------------------------------
    sleep_section = CollapsibleSection("Sleep & Schedule", font)
    sleep_layout = sleep_section.content_layout()

    # Inactivity Timeout
    inactivity_spin = QSpinBox()
    inactivity_spin.setMinimum(10000)
    inactivity_spin.setMaximum(3600000)
    inactivity_spin.setSingleStep(5000)
    inactivity_spin.setSuffix(" ms")
    inactivity_spin.setValue(_get(["behaviors", "sleep", "inactivity_timeout_ms"], 60000))
    inactivity_spin.valueChanged.connect(
        lambda v: _set(["behaviors", "sleep", "inactivity_timeout_ms"], v)
    )
    make_form_row("Inactivity Timeout", inactivity_spin, sleep_layout, font, label_width=160)

    # Enable Schedule
    schedule_cb = QCheckBox("Enable Schedule")
    schedule_cb.setChecked(_get(["behaviors", "sleep", "schedule_enabled"], False))
    schedule_cb.checkStateChanged.connect(
        lambda state: _set(
            ["behaviors", "sleep", "schedule_enabled"],
            state == Qt.CheckState.Checked,
        )
    )
    sleep_layout.addWidget(schedule_cb)

    # Start Time
    start_time_edit = QTimeEdit()
    start_time_edit.setDisplayFormat("HH:mm")
    start_str = _get(["behaviors", "sleep", "schedule_start"], "22:00")
    try:
        sh, sm = start_str.split(":")
        start_time_edit.setTime(QTime(int(sh), int(sm)))
    except (ValueError, AttributeError):
        start_time_edit.setTime(QTime(22, 0))

    def _on_start_time_changed(t: QTime) -> None:
        _set(["behaviors", "sleep", "schedule_start"], t.toString("HH:mm"))

    start_time_edit.timeChanged.connect(_on_start_time_changed)
    make_form_row("Start Time", start_time_edit, sleep_layout, font, label_width=160)

    # End Time
    end_time_edit = QTimeEdit()
    end_time_edit.setDisplayFormat("HH:mm")
    end_str = _get(["behaviors", "sleep", "schedule_end"], "06:00")
    try:
        eh, em = end_str.split(":")
        end_time_edit.setTime(QTime(int(eh), int(em)))
    except (ValueError, AttributeError):
        end_time_edit.setTime(QTime(6, 0))

    def _on_end_time_changed(t: QTime) -> None:
        _set(["behaviors", "sleep", "schedule_end"], t.toString("HH:mm"))

    end_time_edit.timeChanged.connect(_on_end_time_changed)
    make_form_row("End Time", end_time_edit, sleep_layout, font, label_width=160)

    # Time Period Greetings
    greetings_defaults = {
        "morning": "Rise and shine!",
        "afternoon": "Lunch time~",
        "night": "Sleepy time~",
    }
    for period, default_text in greetings_defaults.items():
        greeting_edit = QLineEdit()
        greeting_edit.setText(
            _get(["behaviors", "time_periods", "greetings", period], default_text)
        )

        def _make_greeting_handler(p: str):
            def _handler(v: str) -> None:
                _set(["behaviors", "time_periods", "greetings", p], v)

            return _handler

        greeting_edit.textChanged.connect(_make_greeting_handler(period))
        make_form_row(
            f"{period.capitalize()} Greeting",
            greeting_edit,
            sleep_layout,
            font,
            label_width=160,
        )

    layout.addWidget(sleep_section)
    layout.addStretch()

    return page
