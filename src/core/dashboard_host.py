"""Base dashboard window that integrations can subclass."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QGraphicsBlurEffect,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class DashboardHost(QMainWindow):
    """Base window with stack-based page navigation.

    Integrations subclass this or instantiate directly, adding pages
    via ``add_page`` and navigating with ``push_page`` / ``pop_page``.
    """

    def __init__(
        self,
        window_title: str = "Dashboard",
        window_icon: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        # Init attributes before super().__init__ because Qt may fire
        # changeEvent during window construction.
        self._pages: dict[str, QWidget] = {}
        self._stack: list[str] = []
        self._blur_enabled: bool = False
        self._blur_effect: QGraphicsBlurEffect | None = None

        super().__init__(parent)
        self.setWindowTitle(window_title)
        if window_icon:
            self.setWindowIcon(QIcon(window_icon))

        self._build_chrome()

    def _build_chrome(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar with back button
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        self._back_button = QPushButton("\u2190 Back")
        self._back_button.setVisible(False)
        self._back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_button.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
                color: #888;
                font-size: 13px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #ccc;
            }
        """
        )
        self._back_button.clicked.connect(self.pop_page)
        header_layout.addWidget(self._back_button)
        header_layout.addStretch()

        root.addWidget(header)

        # Content area (stacked widget for pages)
        self._content_stack = QStackedWidget()
        root.addWidget(self._content_stack)

    def add_page(self, name: str, widget: QWidget) -> None:
        """Register a named page."""
        self._pages[name] = widget
        self._content_stack.addWidget(widget)

    def push_page(self, name: str) -> None:
        """Navigate to a named page, pushing onto the back stack."""
        if name not in self._pages:
            raise KeyError(f"Unknown page: {name}")
        self._stack.append(name)
        self._content_stack.setCurrentWidget(self._pages[name])
        self._update_back_button()

    def pop_page(self) -> None:
        """Go back to the previous page in the stack."""
        if len(self._stack) <= 1:
            return
        self._stack.pop()
        current_name = self._stack[-1]
        self._content_stack.setCurrentWidget(self._pages[current_name])
        self._update_back_button()

    def set_blur_on_focus_loss(self, enabled: bool) -> None:
        """Enable/disable blurring window content on focus loss."""
        self._blur_enabled = enabled

    def _update_back_button(self) -> None:
        self._back_button.setVisible(len(self._stack) > 1)

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if not self._blur_enabled:
            return
        from PyQt6.QtCore import QEvent

        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                self._remove_blur()
            else:
                self._apply_blur()

    def _apply_blur(self) -> None:
        if self._blur_effect is None:
            self._blur_effect = QGraphicsBlurEffect()
            self._blur_effect.setBlurRadius(20)
        self._content_stack.setGraphicsEffect(self._blur_effect)
        self._blur_effect.setEnabled(True)

    def _remove_blur(self) -> None:
        if self._blur_effect is not None:
            self._blur_effect.setEnabled(False)
