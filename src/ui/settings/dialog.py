"""Settings dialog — claymorphism themed."""

import copy
import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import load_settings, save_settings

from . import theme
from .tab_behaviors import build_behaviors_tab
from .tab_general import build_general_tab
from .tab_integrations import build_integrations_tab
from .tab_personality import build_personality_tab

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Claymorphism-themed settings dialog with 4 consolidated tabs."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None, integration_manager=None):
        super().__init__(parent)
        self._drag_position = None
        self._integration_manager = integration_manager

        # Load fonts
        heading_font, body_font = theme.load_fonts()
        self._heading_font = heading_font
        self._body_font = body_font

        # Load current settings into mutable buffer
        self._pending = copy.deepcopy(load_settings())

        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.resize(750, 700)
        self.setMinimumSize(550, 400)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)

        self._container = QFrame()
        self._container.setObjectName("settingsContainer")
        self._container.setStyleSheet(
            f"QFrame#settingsContainer {{"
            f"  background-color: {theme.COLORS['background']};"
            f"  border-radius: {theme.CLAY_RADIUS};"
            f"  border: {theme.CLAY_BORDER} solid {theme.COLORS['border_subtle']};"
            f"}}"
        )

        shadow = QGraphicsDropShadowEffect(self._container)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self._container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        container_layout.addWidget(self._build_header())
        container_layout.addWidget(self._build_body(), 1)
        container_layout.addWidget(self._build_footer())

        outer.addWidget(self._container)

    def _build_header(self):
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(48)
        header.setStyleSheet(theme.header_style())

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)

        # Orange dot icon (matches pet theme)
        dot = QLabel()
        dot.setFixedSize(16, 16)
        dot.setStyleSheet(
            f"background: {theme.COLORS['primary']};"
            f"border-radius: 8px;"
            f"border: 2px solid {theme.COLORS['primary_pressed']};"
        )
        layout.addWidget(dot)
        layout.addSpacing(6)

        title = QLabel("Settings")
        title.setObjectName("header_title")
        title.setStyleSheet(
            f"color: #FFFFFF;"
            f"font-family: '{self._heading_font}';"
            f"font-size: 17px;"
            f"font-weight: bold;"
            f"background: transparent;"
        )
        layout.addWidget(title)
        layout.addStretch()

        close_btn = QPushButton("\u2715")
        close_btn.setObjectName("closeButton")
        close_btn.setStyleSheet(theme.close_button_style())
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

        return header

    def _build_body(self):
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

    def _build_sidebar(self):
        sidebar = QListWidget()
        sidebar.setFixedWidth(160)
        sidebar.setStyleSheet(theme.sidebar_style(self._body_font))

        for tab_name in ["General", "Behaviors", "Integrations", "AI & Personality"]:
            item = QListWidgetItem(tab_name)
            item.setSizeHint(item.sizeHint())
            sidebar.addItem(item)

        return sidebar

    def _build_content_area(self):
        stacked = QStackedWidget()
        stacked.setStyleSheet(f"background-color: {theme.COLORS['background']};")

        tabs = [
            build_general_tab(self._pending, self._body_font),
            build_behaviors_tab(self._pending, self._body_font),
            build_integrations_tab(self._pending, self._body_font, self._integration_manager),
            build_personality_tab(self._pending, self._body_font),
        ]

        for page in tabs:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(page)
            scroll.setStyleSheet(theme.scroll_area_style())
            stacked.addWidget(scroll)

        return stacked

    def _build_footer(self):
        footer = QWidget()
        footer.setObjectName("footer")
        footer.setFixedHeight(56)
        footer.setStyleSheet(theme.footer_style())

        layout = QHBoxLayout(footer)
        layout.addStretch()

        ok_btn = QPushButton("Ok")
        ok_btn.setObjectName("okButton")
        ok_btn.setStyleSheet(theme.ok_button_style(self._body_font))
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self._on_ok)
        layout.addWidget(ok_btn)

        layout.addSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setStyleSheet(theme.cancel_button_style(self._body_font))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        layout.addStretch()

        grip = QSizeGrip(self)
        grip.setStyleSheet("background: transparent;")
        grip.setFixedSize(16, 16)
        layout.addWidget(grip, 0, Qt.AlignmentFlag.AlignBottom)

        return footer

    def _on_ok(self):
        save_settings(self._pending)
        self.settings_changed.emit(self._pending)
        self.accept()

    # --- Drag support ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
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

    # --- Center on screen ---
    def showEvent(self, event):
        super().showEvent(event)
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.x() + (geo.width() - self.width()) // 2,
                geo.y() + (geo.height() - self.height()) // 2,
            )
