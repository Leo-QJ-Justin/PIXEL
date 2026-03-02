import asyncio

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from config import BEHAVIORS_DIR
from src.core.behavior_registry import BehaviorRegistry
from src.core.integration_manager import IntegrationManager


class TrayIcon(QSystemTrayIcon):
    """System tray icon for desktop pet."""

    settings_changed = pyqtSignal(dict)

    def __init__(
        self,
        pet_widget,
        integration_manager: IntegrationManager,
        behavior_registry: BehaviorRegistry | None = None,
    ):
        super().__init__()
        self._pet_widget = pet_widget
        self._integration_manager = integration_manager
        self._behavior_registry = behavior_registry
        self._integration_actions: dict[str, QAction] = {}

        self._setup_icon()
        self._setup_menu()

    def _setup_icon(self):
        idle_media_dir = BEHAVIORS_DIR / "idle" / "media"

        if idle_media_dir.exists():
            # Try PNG first, then GIF
            media_files = sorted(idle_media_dir.glob("*.png"))
            if not media_files:
                media_files = sorted(idle_media_dir.glob("*.gif"))
            if media_files:
                self.setIcon(QIcon(str(media_files[0])))

        self.setToolTip("Desktop Pet")

    def _setup_menu(self):
        menu = QMenu()

        show_action = QAction("Show", menu)
        show_action.triggered.connect(self._toggle_visibility)
        menu.addAction(show_action)

        reset_action = QAction("Reset Position", menu)
        reset_action.triggered.connect(self._pet_widget._move_to_default_position)
        menu.addAction(reset_action)

        settings_action = QAction("Settings...", menu)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        integrations_menu = QMenu("Integrations", menu)
        self._build_integrations_menu(integrations_menu)
        menu.addMenu(integrations_menu)

        menu.addSeparator()

        test_alert_action = QAction("Test Alert", menu)
        test_alert_action.triggered.connect(self._test_alert)
        menu.addAction(test_alert_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _build_integrations_menu(self, menu: QMenu):
        integrations = self._integration_manager.list_integrations()

        if not integrations:
            no_integrations = QAction("No integrations loaded", menu)
            no_integrations.setEnabled(False)
            menu.addAction(no_integrations)
            return

        for name in integrations:
            integration = self._integration_manager.get_integration(name)
            if integration:
                action = QAction(integration.display_name, menu)
                action.setCheckable(True)
                action.setChecked(integration.enabled)
                action.triggered.connect(
                    lambda checked, n=name: self._toggle_integration(n, checked)
                )
                menu.addAction(action)
                self._integration_actions[name] = action

    def _toggle_integration(self, name: str, enabled: bool):
        integration = self._integration_manager.get_integration(name)
        if not integration:
            return

        integration.enabled = enabled

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        if enabled:
            loop.create_task(self._integration_manager.start(name))
        else:
            loop.create_task(self._integration_manager.stop(name))

    def _toggle_visibility(self):
        if self._pet_widget.isVisible():
            self._pet_widget.hide()
        else:
            self._pet_widget.show()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_visibility()

    def _test_alert(self):
        if self._behavior_registry:
            self._behavior_registry.trigger("alert", {"sender": "Test User"})

    def _open_settings(self):
        from src.ui.settings_dialog import SettingsDialog

        dialog = SettingsDialog()
        dialog.settings_changed.connect(self.settings_changed)
        dialog.exec()

    def _quit_app(self):
        from PyQt6.QtWidgets import QApplication

        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._integration_manager.stop_all())
        except RuntimeError:
            pass

        QApplication.quit()
