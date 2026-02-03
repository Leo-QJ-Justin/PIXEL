from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from config import SPRITES_DIR


class TrayIcon(QSystemTrayIcon):
    """System tray icon for Haro desktop pet."""

    def __init__(self, haro_widget):
        super().__init__()
        self._haro_widget = haro_widget

        self._setup_icon()
        self._setup_menu()

    def _setup_icon(self):
        """Set the tray icon."""
        idle_sprites = sorted(SPRITES_DIR.glob("idle*.png"))
        if idle_sprites:
            self.setIcon(QIcon(str(idle_sprites[0])))
        self.setToolTip("Haro Desktop Pet")

    def _setup_menu(self):
        """Create the tray icon context menu."""
        menu = QMenu()

        # Show/Hide action
        show_action = QAction("Show Haro", menu)
        show_action.triggered.connect(self._toggle_visibility)
        menu.addAction(show_action)

        # Reset position
        reset_action = QAction("Reset Position", menu)
        reset_action.triggered.connect(self._haro_widget._move_to_default_position)
        menu.addAction(reset_action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

        # Double-click to toggle visibility
        self.activated.connect(self._on_activated)

    def _toggle_visibility(self):
        """Toggle Haro widget visibility."""
        if self._haro_widget.isVisible():
            self._haro_widget.hide()
        else:
            self._haro_widget.show()

    def _on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_visibility()

    def _quit_app(self):
        """Quit the application."""
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
