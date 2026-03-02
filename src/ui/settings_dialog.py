"""MapleStory-themed settings dialog using QSS styling."""

import copy
import logging
from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, QTime, pyqtSignal
from PyQt6.QtGui import QColor, QFontDatabase
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from config import load_settings, save_settings

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"

# ---------------------------------------------------------------------------
# QSS Stylesheet constants
# ---------------------------------------------------------------------------

_CONTENT_STYLE = """
QLineEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 10pt;
}
QLineEdit:focus {
    border: 2px solid #0088AA;
}
QCheckBox {
    color: #555555;
    font-size: 10pt;
    spacing: 8px;
    background: transparent;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #cccccc;
    border-radius: 3px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #FFCC00;
    border-color: #CC9900;
}
QComboBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 10pt;
    min-width: 120px;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    selection-background-color: #0088AA;
    selection-color: #ffffff;
}
QSlider::groove:horizontal {
    border: 1px solid #cccccc;
    height: 6px;
    background: #dddddd;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #FFCC00;
    border: 1px solid #CC9900;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #FFCC00;
    border-radius: 3px;
}
QTimeEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 10pt;
}
QSpinBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 10pt;
}
"""

_SIDEBAR_STYLE = """
QListWidget {{
    background-color: #2a2a2a;
    border: none;
    outline: none;
    font-family: {font};
    font-size: 11pt;
    color: #cccccc;
    padding: 4px 0;
    border-right: 1px solid #111111;
}}
QListWidget::item {{
    padding: 12px 16px;
    border-left: 3px solid transparent;
}}
QListWidget::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #0088AA, stop:1 #005577);
    border-left: 3px solid #00AAFF;
    color: #ffffff;
    font-weight: bold;
}}
QListWidget::item:hover:!selected {{
    background-color: #333333;
}}
"""

_OK_BUTTON_STYLE = """
QPushButton#okButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #AADD00, stop:1 #669900);
    border: 2px solid #446600;
    border-radius: 4px;
    color: #ffffff;
    font-weight: bold;
    font-size: 10pt;
    padding: 8px 24px;
    min-width: 80px;
}
QPushButton#okButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #BBEE11, stop:1 #77AA00);
}
QPushButton#okButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #669900, stop:1 #446600);
}
"""

_CANCEL_BUTTON_STYLE = """
QPushButton#cancelButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #888888, stop:1 #555555);
    border: 2px solid #555555;
    border-radius: 4px;
    color: #ffffff;
    font-weight: bold;
    font-size: 10pt;
    padding: 8px 24px;
    min-width: 80px;
}
QPushButton#cancelButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #999999, stop:1 #666666);
}
QPushButton#cancelButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #555555, stop:1 #444444);
}
"""

_CLOSE_BUTTON_STYLE = """
QPushButton#closeButton {
    background: transparent;
    border: none;
    color: #999999;
    font-size: 14pt;
    font-weight: bold;
    padding: 4px 8px;
}
QPushButton#closeButton:hover {
    color: #ffffff;
}
"""


class SettingsDialog(QDialog):
    """MapleStory-themed settings dialog."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._drag_position: QPoint | None = None

        # Load custom font
        self._font_family = self._load_font()

        # Load current settings into a mutable buffer
        self._pending = copy.deepcopy(load_settings())

        self._setup_window()
        self._build_ui()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _load_font(self) -> str:
        font_path = ASSETS_DIR / "fonts" / "MPLUSRounded1c-Regular.ttf"
        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
        return "sans-serif"

    def _setup_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.resize(750, 700)
        self.setMinimumSize(550, 400)

    # ------------------------------------------------------------------
    # Top-level layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)

        # Container frame (the visible "window")
        self._container = QFrame()
        self._container.setObjectName("settingsContainer")
        self._container.setStyleSheet(
            "QFrame#settingsContainer {"
            "  background-color: #222222;"
            "  border-radius: 8px;"
            "  border: 1px solid #444444;"
            "}"
        )

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self._container)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 120))
        self._container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        container_layout.addWidget(self._build_header())
        container_layout.addWidget(self._build_body(), 1)
        container_layout.addWidget(self._build_footer())

        outer.addWidget(self._container)

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            "  stop:0 #444444, stop:1 #222222);"
            "border-top-left-radius: 8px;"
            "border-top-right-radius: 8px;"
            "border-bottom: 1px solid #555555;"
        )

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)

        # Yellow dot icon
        dot = QLabel()
        dot.setFixedSize(16, 16)
        dot.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            "  stop:0 #FFE066, stop:1 #CCAA00);"
            "border-radius: 8px;"
            "border: 1px solid #AA8800;"
        )
        layout.addWidget(dot)
        layout.addSpacing(6)

        # Title
        title = QLabel("Options")
        title.setStyleSheet(
            f"color: #FFCC00;"
            f"font-family: '{self._font_family}';"
            f"font-size: 14pt;"
            f"font-weight: bold;"
            f"background: transparent;"
        )
        layout.addWidget(title)
        layout.addStretch()

        # Close button
        close_btn = QPushButton("\u2715")
        close_btn.setObjectName("closeButton")
        close_btn.setStyleSheet(_CLOSE_BUTTON_STYLE)
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

        return header

    # ------------------------------------------------------------------
    # Body (sidebar + content)
    # ------------------------------------------------------------------

    def _build_body(self) -> QWidget:
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = self._build_sidebar()
        self._stacked = self._build_content_area()

        layout.addWidget(self._sidebar)
        layout.addWidget(self._stacked, 1)

        self._sidebar.currentRowChanged.connect(self._stacked.setCurrentIndex)
        self._sidebar.setCurrentRow(0)

        return body

    def _build_sidebar(self) -> QListWidget:
        sidebar = QListWidget()
        sidebar.setFixedWidth(150)
        sidebar.setStyleSheet(_SIDEBAR_STYLE.format(font=self._font_family))

        for tab_name in ["General", "Behaviors", "Time / Schedule"]:
            item = QListWidgetItem(tab_name)
            item.setSizeHint(item.sizeHint())
            sidebar.addItem(item)

        return sidebar

    def _build_content_area(self) -> QStackedWidget:
        stacked = QStackedWidget()
        stacked.setStyleSheet("background-color: #dcdcdc;")

        tabs = [
            self._build_general_tab,
            self._build_behaviors_tab,
            self._build_time_schedule_tab,
        ]
        for builder in tabs:
            page = builder()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(page)
            scroll.setStyleSheet(
                "QScrollArea { border: none; background-color: #eeeeee; }"
                "QScrollBar:vertical {"
                "  background: #dcdcdc; width: 10px; border: none;"
                "}"
                "QScrollBar::handle:vertical {"
                "  background: #999999; border-radius: 5px; min-height: 20px;"
                "}"
                "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {"
                "  height: 0;"
                "}"
            )
            stacked.addWidget(scroll)

        return stacked

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setFixedHeight(56)
        footer.setStyleSheet(
            "background-color: #222222;"
            "border-top: 1px solid #444444;"
            "border-bottom-left-radius: 8px;"
            "border-bottom-right-radius: 8px;"
        )

        layout = QHBoxLayout(footer)
        layout.addStretch()

        ok_btn = QPushButton("Ok")
        ok_btn.setObjectName("okButton")
        ok_btn.setStyleSheet(_OK_BUTTON_STYLE)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self._on_ok)
        layout.addWidget(ok_btn)

        layout.addSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setStyleSheet(_CANCEL_BUTTON_STYLE)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        layout.addStretch()

        # Resize grip in bottom-right corner
        grip = QSizeGrip(self)
        grip.setStyleSheet("background: transparent;")
        grip.setFixedSize(16, 16)
        layout.addWidget(grip, 0, Qt.AlignmentFlag.AlignBottom)

        return footer

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_nested(self, keys: list[str], value):
        """Update a nested key in the pending settings dict."""
        d = self._pending
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    def _get_nested(self, keys: list[str], default=None):
        """Read a nested key from the pending settings dict."""
        d = self._pending
        for k in keys[:-1]:
            d = d.get(k, {})
        return d.get(keys[-1], default)

    def _make_section(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        """Create a titled section box."""
        group = QWidget()
        group.setStyleSheet(
            "QWidget#sectionBox {"
            "  background-color: #e5e5e5;"
            "  border-radius: 6px;"
            "  border: 1px solid #cccccc;"
            "}"
        )
        group.setObjectName("sectionBox")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        heading = QLabel(title)
        heading.setStyleSheet(
            f"color: #333333; font-size: 12pt; font-weight: bold;"
            f"font-family: '{self._font_family}'; background: transparent;"
            f"border: none; border-bottom: 1px solid #bbbbbb;"
            f"padding-bottom: 4px;"
        )
        layout.addWidget(heading)

        return group, layout

    def _make_form_row(self, label_text: str, widget: QWidget, layout: QVBoxLayout):
        """Add a horizontal label + control row to a layout."""
        row = QHBoxLayout()
        row.setSpacing(12)
        label = QLabel(label_text)
        label.setFixedWidth(120)
        label.setStyleSheet(
            f"color: #555555; font-size: 10pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
            f"border: none;"
        )
        row.addWidget(label)
        row.addWidget(widget, 1)
        layout.addLayout(row)

    def _make_tab_page(self) -> tuple[QWidget, QVBoxLayout]:
        """Create a scrollable tab page widget with shared content styling."""
        page = QWidget()
        page.setStyleSheet(
            f"QWidget {{ background-color: #eeeeee;"
            f"  font-family: '{self._font_family}'; }}\n" + _CONTENT_STYLE
        )
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        return page, layout

    # ------------------------------------------------------------------
    # Tab: General
    # ------------------------------------------------------------------

    def _build_general_tab(self) -> QWidget:
        page, layout = self._make_tab_page()

        # --- Profile section ---
        section, sec_layout = self._make_section("Profile")
        name_edit = QLineEdit(self._get_nested(["user_name"], ""))
        name_edit.setPlaceholderText("Enter username...")
        name_edit.textChanged.connect(lambda text: self._set_nested(["user_name"], text))
        self._make_form_row("User Name", name_edit, sec_layout)
        layout.addWidget(section)

        # --- Window section ---
        section, sec_layout = self._make_section("Window")

        aot_cb = QCheckBox("Always on top")
        aot_cb.setChecked(self._get_nested(["general", "always_on_top"], True))
        aot_cb.toggled.connect(lambda v: self._set_nested(["general", "always_on_top"], v))
        sec_layout.addWidget(aot_cb)

        min_cb = QCheckBox("Start minimized")
        min_cb.setChecked(self._get_nested(["general", "start_minimized"], False))
        min_cb.toggled.connect(lambda v: self._set_nested(["general", "start_minimized"], v))
        sec_layout.addWidget(min_cb)

        boot_cb = QCheckBox("Start on boot")
        boot_cb.setChecked(self._get_nested(["general", "start_on_boot"], False))
        boot_cb.toggled.connect(lambda v: self._set_nested(["general", "start_on_boot"], v))
        sec_layout.addWidget(boot_cb)

        facing_combo = QComboBox()
        facing_combo.addItem("Right", "right")
        facing_combo.addItem("Left", "left")
        current = self._get_nested(["general", "sprite_default_facing"], "right")
        idx = facing_combo.findData(current)
        if idx >= 0:
            facing_combo.setCurrentIndex(idx)
        facing_combo.currentIndexChanged.connect(
            lambda: self._set_nested(
                ["general", "sprite_default_facing"],
                facing_combo.currentData(),
            )
        )
        self._make_form_row("Default Facing", facing_combo, sec_layout)

        layout.addWidget(section)

        # --- Speech Bubble section ---
        section, sec_layout = self._make_section("Speech Bubble")

        bubble_cb = QCheckBox("Enabled")
        bubble_cb.setChecked(self._get_nested(["general", "speech_bubble", "enabled"], True))
        bubble_cb.toggled.connect(
            lambda v: self._set_nested(["general", "speech_bubble", "enabled"], v)
        )
        sec_layout.addWidget(bubble_cb)

        duration_val = self._get_nested(["general", "speech_bubble", "duration_ms"], 3000)
        slider_row = QHBoxLayout()
        slider_row.setSpacing(8)
        dur_label = QLabel("Duration")
        dur_label.setFixedWidth(120)
        dur_label.setStyleSheet(
            f"color: #555555; font-size: 10pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
            f"border: none;"
        )
        slider_row.addWidget(dur_label)

        dur_slider = QSlider(Qt.Orientation.Horizontal)
        dur_slider.setRange(0, 10000)
        dur_slider.setSingleStep(100)
        dur_slider.setValue(duration_val)
        slider_row.addWidget(dur_slider, 1)

        dur_value_label = QLabel(f"{duration_val} ms")
        dur_value_label.setFixedWidth(70)
        dur_value_label.setStyleSheet(
            "color: #333333; font-size: 10pt; background: transparent;" "border: none;"
        )
        slider_row.addWidget(dur_value_label)

        def on_dur_changed(v):
            dur_value_label.setText(f"{v} ms")
            self._set_nested(["general", "speech_bubble", "duration_ms"], v)

        dur_slider.valueChanged.connect(on_dur_changed)
        sec_layout.addLayout(slider_row)

        layout.addWidget(section)

        layout.addStretch()
        return page

    # ------------------------------------------------------------------
    # Tab: Behaviors
    # ------------------------------------------------------------------

    def _build_behaviors_tab(self) -> QWidget:
        page, layout = self._make_tab_page()

        # --- Fly / Wander section ---
        section, sec_layout = self._make_section("Fly / Wander")

        # Wander chance slider (0-100 %, stored as 0.0-1.0)
        chance_val = self._get_nested(["behaviors", "wander", "wander_chance"], 0.3)
        chance_pct = int(chance_val * 100)

        slider_row = QHBoxLayout()
        slider_row.setSpacing(8)
        chance_label = QLabel("Wander Chance")
        chance_label.setFixedWidth(120)
        chance_label.setStyleSheet(
            f"color: #555555; font-size: 10pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
            f"border: none;"
        )
        slider_row.addWidget(chance_label)

        chance_slider = QSlider(Qt.Orientation.Horizontal)
        chance_slider.setRange(0, 100)
        chance_slider.setValue(chance_pct)
        slider_row.addWidget(chance_slider, 1)

        chance_value_label = QLabel(f"{chance_pct}%")
        chance_value_label.setFixedWidth(50)
        chance_value_label.setStyleSheet(
            "color: #333333; font-size: 10pt; background: transparent;" "border: none;"
        )
        slider_row.addWidget(chance_value_label)

        def on_chance_changed(v):
            chance_value_label.setText(f"{v}%")
            self._set_nested(["behaviors", "wander", "wander_chance"], v / 100.0)

        chance_slider.valueChanged.connect(on_chance_changed)
        sec_layout.addLayout(slider_row)

        # Interval min/max
        interval_row = QHBoxLayout()
        interval_row.setSpacing(8)
        interval_label = QLabel("Interval (ms)")
        interval_label.setFixedWidth(120)
        interval_label.setStyleSheet(
            f"color: #555555; font-size: 10pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
            f"border: none;"
        )
        interval_row.addWidget(interval_label)

        min_spin = QSpinBox()
        min_spin.setRange(1000, 60000)
        min_spin.setSingleStep(1000)
        min_spin.setValue(self._get_nested(["behaviors", "wander", "wander_interval_min_ms"], 5000))
        min_spin.valueChanged.connect(
            lambda v: self._set_nested(["behaviors", "wander", "wander_interval_min_ms"], v)
        )
        interval_row.addWidget(min_spin, 1)

        to_label = QLabel("to")
        to_label.setStyleSheet(
            "color: #555555; font-size: 10pt; background: transparent;" "border: none;"
        )
        to_label.setFixedWidth(20)
        interval_row.addWidget(to_label)

        max_spin = QSpinBox()
        max_spin.setRange(1000, 60000)
        max_spin.setSingleStep(1000)
        max_spin.setValue(
            self._get_nested(["behaviors", "wander", "wander_interval_max_ms"], 15000)
        )
        max_spin.valueChanged.connect(
            lambda v: self._set_nested(["behaviors", "wander", "wander_interval_max_ms"], v)
        )
        interval_row.addWidget(max_spin, 1)

        sec_layout.addLayout(interval_row)
        layout.addWidget(section)

        # --- Wave section ---
        section, sec_layout = self._make_section("Wave")

        greeting_edit = QLineEdit(self._get_nested(["behaviors", "wave", "greeting"], "Hello!"))
        greeting_edit.textChanged.connect(
            lambda text: self._set_nested(["behaviors", "wave", "greeting"], text)
        )
        self._make_form_row("Greeting", greeting_edit, sec_layout)

        layout.addWidget(section)

        layout.addStretch()
        return page

    # ------------------------------------------------------------------
    # Tab: Time / Schedule
    # ------------------------------------------------------------------

    def _build_time_schedule_tab(self) -> QWidget:
        page, layout = self._make_tab_page()

        # --- Sleep section ---
        section, sec_layout = self._make_section("Sleep Schedule")

        # Inactivity timeout
        timeout_spin = QSpinBox()
        timeout_spin.setRange(10000, 3600000)
        timeout_spin.setSingleStep(5000)
        timeout_spin.setSuffix(" ms")
        timeout_spin.setValue(
            self._get_nested(["behaviors", "sleep", "inactivity_timeout_ms"], 60000)
        )
        timeout_spin.valueChanged.connect(
            lambda v: self._set_nested(["behaviors", "sleep", "inactivity_timeout_ms"], v)
        )
        self._make_form_row("Inactivity Timeout", timeout_spin, sec_layout)

        schedule_cb = QCheckBox("Enable Schedule")
        schedule_cb.setChecked(self._get_nested(["behaviors", "sleep", "schedule_enabled"], False))
        schedule_cb.toggled.connect(
            lambda v: self._set_nested(["behaviors", "sleep", "schedule_enabled"], v)
        )
        sec_layout.addWidget(schedule_cb)

        # Start / End time
        time_row = QHBoxLayout()
        time_row.setSpacing(12)

        start_label = QLabel("Start")
        start_label.setFixedWidth(40)
        start_label.setStyleSheet(
            "color: #555555; font-size: 10pt; background: transparent;" "border: none;"
        )
        time_row.addWidget(start_label)

        start_time = QTimeEdit()
        start_time.setDisplayFormat("HH:mm")
        start_time.setTime(
            QTime.fromString(
                self._get_nested(["behaviors", "sleep", "schedule_start"], "22:00"),
                "HH:mm",
            )
        )
        start_time.timeChanged.connect(
            lambda t: self._set_nested(
                ["behaviors", "sleep", "schedule_start"],
                t.toString("HH:mm"),
            )
        )
        time_row.addWidget(start_time, 1)

        end_label = QLabel("End")
        end_label.setFixedWidth(40)
        end_label.setStyleSheet(
            "color: #555555; font-size: 10pt; background: transparent;" "border: none;"
        )
        time_row.addWidget(end_label)

        end_time = QTimeEdit()
        end_time.setDisplayFormat("HH:mm")
        end_time.setTime(
            QTime.fromString(
                self._get_nested(["behaviors", "sleep", "schedule_end"], "06:00"),
                "HH:mm",
            )
        )
        end_time.timeChanged.connect(
            lambda t: self._set_nested(
                ["behaviors", "sleep", "schedule_end"],
                t.toString("HH:mm"),
            )
        )
        time_row.addWidget(end_time, 1)

        sec_layout.addLayout(time_row)
        layout.addWidget(section)

        # --- Time Period Greetings section ---
        section, sec_layout = self._make_section("Time Period Greetings")

        for period, default in [
            ("morning", "Good morning!"),
            ("afternoon", "Good afternoon!"),
            ("night", "Good night!"),
        ]:
            edit = QLineEdit(
                self._get_nested(
                    ["behaviors", "time_periods", "greetings", period],
                    default,
                )
            )
            edit.textChanged.connect(
                lambda text, p=period: self._set_nested(
                    ["behaviors", "time_periods", "greetings", p], text
                )
            )
            self._make_form_row(period.capitalize(), edit, sec_layout)

        layout.addWidget(section)

        layout.addStretch()
        return page

    # ------------------------------------------------------------------
    # Ok / Cancel
    # ------------------------------------------------------------------

    def _on_ok(self):
        save_settings(self._pending)
        self.settings_changed.emit(self._pending)
        self.accept()

    # ------------------------------------------------------------------
    # Drag support
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 4px outer margin + 48px header = 52px
            if event.position().y() <= 52:
                self._drag_position = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_position = None
        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------
    # Center on screen
    # ------------------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.x() + (geo.width() - self.width()) // 2,
                geo.y() + (geo.height() - self.height()) // 2,
            )
