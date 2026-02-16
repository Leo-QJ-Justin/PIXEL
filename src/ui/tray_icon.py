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
        """Set the tray icon from the first idle sprite."""
        idle_sprites_dir = BEHAVIORS_DIR / "idle" / "sprites"

        if idle_sprites_dir.exists():
            sprite_files = sorted(idle_sprites_dir.glob("*.png"))
            if sprite_files:
                self.setIcon(QIcon(str(sprite_files[0])))

        self.setToolTip("Desktop Pet")

    def _setup_menu(self):
        """Create the tray icon context menu."""
        menu = QMenu()

        # Show/Hide action
        show_action = QAction("Show", menu)
        show_action.triggered.connect(self._toggle_visibility)
        menu.addAction(show_action)

        # Reset position
        reset_action = QAction("Reset Position", menu)
        reset_action.triggered.connect(self._pet_widget._move_to_default_position)
        menu.addAction(reset_action)

        # Settings
        settings_action = QAction("Settings...", menu)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        # Integrations submenu
        integrations_menu = QMenu("Integrations", menu)
        self._build_integrations_menu(integrations_menu)
        menu.addMenu(integrations_menu)

        # API Usage submenu (lazy-populated on open)
        self._api_usage_menu = QMenu("API Usage", menu)
        self._api_usage_menu.aboutToShow.connect(self._refresh_api_usage_menu)
        menu.addMenu(self._api_usage_menu)

        menu.addSeparator()

        # Test Alert action
        test_alert_action = QAction("Test Alert", menu)
        test_alert_action.triggered.connect(self._test_alert)
        menu.addAction(test_alert_action)

        # Test Rainy action
        test_rainy_action = QAction("Test Rainy", menu)
        test_rainy_action.triggered.connect(self._test_rainy)
        menu.addAction(test_rainy_action)

        # Test Sunny action
        test_sunny_action = QAction("Test Sunny", menu)
        test_sunny_action.triggered.connect(self._test_sunny)
        menu.addAction(test_sunny_action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

        # Double-click to toggle visibility
        self.activated.connect(self._on_activated)

    def _build_integrations_menu(self, menu: QMenu):
        """Build the integrations submenu with enable/disable toggles."""
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
        """Toggle an integration on or off."""
        integration = self._integration_manager.get_integration(name)
        if not integration:
            return

        integration.enabled = enabled

        # Get the current event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        if enabled:
            # Start the integration
            loop.create_task(self._integration_manager.start(name))
        else:
            # Stop the integration
            loop.create_task(self._integration_manager.stop(name))

    def _toggle_visibility(self):
        """Toggle pet widget visibility."""
        if self._pet_widget.isVisible():
            self._pet_widget.hide()
        else:
            self._pet_widget.show()

    def _on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_visibility()

    def _test_alert(self):
        """Trigger a test alert for debugging."""
        if self._behavior_registry:
            self._behavior_registry.trigger("alert", {"sender": "Test User"})

    def _test_rainy(self):
        """Trigger a test rainy behavior for debugging."""
        if self._behavior_registry:
            self._behavior_registry.trigger(
                "rainy",
                {
                    "condition": "rainy",
                    "description": "Light rain",
                    "temperature": "65°F",
                    "city": "Test City",
                },
            )

    def _test_sunny(self):
        """Trigger a test sunny behavior for debugging."""
        if self._behavior_registry:
            self._behavior_registry.trigger(
                "sunny",
                {
                    "condition": "sunny",
                    "description": "Clear sky",
                    "temperature": "85°F",
                    "city": "Test City",
                },
            )

    def _refresh_api_usage_menu(self):
        """Populate API Usage submenu with current counts."""
        self._api_usage_menu.clear()

        gcal = self._integration_manager.get_integration("google_calendar")
        if gcal is None or not hasattr(gcal, "usage_tracker"):
            no_data = QAction("No calendar integration", self._api_usage_menu)
            no_data.setEnabled(False)
            self._api_usage_menu.addAction(no_data)
            return

        usage = gcal.usage_tracker.get_usage()
        limit = usage.get("limit", 9500)
        month = usage.get("month", "")

        routes_action = QAction(
            f"Routes API: {usage.get('routes_api', 0)} / {limit}",
            self._api_usage_menu,
        )
        routes_action.setEnabled(False)
        self._api_usage_menu.addAction(routes_action)

        geocoding_action = QAction(
            f"Geocoding API: {usage.get('geocoding_api', 0)} / {limit}",
            self._api_usage_menu,
        )
        geocoding_action.setEnabled(False)
        self._api_usage_menu.addAction(geocoding_action)

        if month:
            self._api_usage_menu.addSeparator()
            # Calculate next reset month
            try:
                from datetime import datetime

                dt = datetime.strptime(month, "%Y-%m")
                next_month = dt.month % 12 + 1
                next_year = dt.year + (1 if next_month == 1 else 0)
                reset_str = f"{next_year}-{next_month:02d}"
            except ValueError:
                reset_str = "next month"
            reset_action = QAction(f"Resets: {reset_str}", self._api_usage_menu)
            reset_action.setEnabled(False)
            self._api_usage_menu.addAction(reset_action)

    def _open_settings(self):
        """Open the settings dialog."""
        from src.ui.settings_dialog import SettingsDialog

        dialog = SettingsDialog()
        dialog.settings_changed.connect(self.settings_changed)
        dialog.exec()

    def _quit_app(self):
        """Quit the application."""
        from PyQt6.QtWidgets import QApplication

        # Stop all integrations before quitting
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._integration_manager.stop_all())
        except RuntimeError:
            pass

        QApplication.quit()
