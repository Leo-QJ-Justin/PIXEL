import asyncio

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from config import BEHAVIORS_DIR
from src.core.behavior_registry import CHARACTERS, BehaviorRegistry
from src.core.integration_manager import IntegrationManager


class TrayIcon(QSystemTrayIcon):
    """System tray icon for Haro desktop pet."""

    def __init__(
        self,
        haro_widget,
        integration_manager: IntegrationManager,
        behavior_registry: BehaviorRegistry | None = None,
    ):
        super().__init__()
        self._haro_widget = haro_widget
        self._integration_manager = integration_manager
        self._behavior_registry = behavior_registry
        self._integration_actions: dict[str, QAction] = {}
        self._character_actions: dict[str, QAction] = {}

        self._setup_icon()
        self._setup_menu()

        # Update tray icon when character changes
        if self._behavior_registry:
            self._behavior_registry.character_changed.connect(self._on_character_changed)

    def _setup_icon(self):
        """Set the tray icon based on current character."""
        character = "haro"
        if self._behavior_registry:
            character = self._behavior_registry.character

        prefix = CHARACTERS.get(character, "")
        idle_sprites_dir = BEHAVIORS_DIR / "idle" / "sprites"

        if idle_sprites_dir.exists():
            # Find sprites matching current character
            if prefix:
                sprite_files = sorted(idle_sprites_dir.glob(f"{prefix}*.png"))
            else:
                # For default character, exclude other character prefixes
                other_prefixes = [p for p in CHARACTERS.values() if p]
                sprite_files = [
                    f
                    for f in sorted(idle_sprites_dir.glob("*.png"))
                    if not any(f.name.startswith(p) for p in other_prefixes)
                ]

            if sprite_files:
                self.setIcon(QIcon(str(sprite_files[0])))

        self.setToolTip(f"{character.title()} Desktop Pet")

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

        # Integrations submenu
        integrations_menu = QMenu("Integrations", menu)
        self._build_integrations_menu(integrations_menu)
        menu.addMenu(integrations_menu)

        # Character submenu
        character_menu = QMenu("Character", menu)
        self._build_character_menu(character_menu)
        menu.addMenu(character_menu)

        menu.addSeparator()

        # Test Alert action
        test_alert_action = QAction("Test Alert", menu)
        test_alert_action.triggered.connect(self._test_alert)
        menu.addAction(test_alert_action)

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

    def _build_character_menu(self, menu: QMenu):
        """Build the character submenu for switching characters."""
        current_character = "haro"
        if self._behavior_registry:
            current_character = self._behavior_registry.character

        for character_name in CHARACTERS.keys():
            action = QAction(character_name.title(), menu)
            action.setCheckable(True)
            action.setChecked(character_name == current_character)
            action.triggered.connect(lambda checked, c=character_name: self._switch_character(c))
            menu.addAction(action)
            self._character_actions[character_name] = action

    def _switch_character(self, character: str):
        """Switch to a different character."""
        if self._behavior_registry:
            self._behavior_registry.set_character(character)

    def _on_character_changed(self, character: str):
        """Handle character change - update menu checkmarks and tray icon."""
        # Update checkmarks
        for name, action in self._character_actions.items():
            action.setChecked(name == character)

        # Update tray icon
        self._setup_icon()

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
        """Toggle Haro widget visibility."""
        if self._haro_widget.isVisible():
            self._haro_widget.hide()
        else:
            self._haro_widget.show()

    def _on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_visibility()

    def _test_alert(self):
        """Trigger a test alert for debugging."""
        if self._behavior_registry:
            self._behavior_registry.trigger("alert", {"sender": "Test User"})

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
