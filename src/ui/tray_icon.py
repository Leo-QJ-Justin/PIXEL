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
        pomodoro_widget=None,
        panel_host=None,
    ):
        super().__init__()
        self._pet_widget = pet_widget
        self._integration_manager = integration_manager
        self._behavior_registry = behavior_registry
        self._pomodoro_widget = pomodoro_widget
        self._panel_host = panel_host
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

        # Panel entries (React UI)
        if self._panel_host is not None:
            journal_action = QAction("Dashboard", menu)
            journal_action.triggered.connect(
                lambda: self._panel_host.open_panel("journal")
            )
            menu.addAction(journal_action)

        # Dashboard entries for integrations that provide one (legacy, non-React)
        dashboards = self._integration_manager.get_dashboards()
        if dashboards:
            for name, dashboard in dashboards.items():
                # Skip journal dashboard — now handled by React panel
                if name == "journal":
                    continue
                integration = self._integration_manager.get_integration(name)
                label = f"{integration.display_name} Dashboard" if integration else name
                dash_action = QAction(label, menu)
                dash_action.triggered.connect(lambda checked, d=dashboard: self._show_dashboard(d))
                menu.addAction(dash_action)

        menu.addSeparator()

        # Pomodoro: route through React panel if available, else old widget
        if self._panel_host is not None:
            pomodoro_menu = QMenu("Pomodoro", menu)
            show_action = QAction("Show Timer", pomodoro_menu)
            show_action.triggered.connect(
                lambda: self._panel_host.open_panel("pomodoro")
            )
            pomodoro_menu.addAction(show_action)
            # Keep start/skip actions wired to the integration directly
            pomodoro_integration = self._integration_manager.get_integration("pomodoro")
            if pomodoro_integration:
                start_action = QAction("Start Session", pomodoro_menu)
                start_action.triggered.connect(pomodoro_integration.start_session)
                pomodoro_menu.addAction(start_action)
                skip_action = QAction("Skip", pomodoro_menu)
                skip_action.triggered.connect(pomodoro_integration.skip)
                pomodoro_menu.addAction(skip_action)
            menu.addMenu(pomodoro_menu)
        elif self._pomodoro_widget:
            pomodoro_menu = QMenu("Pomodoro", menu)
            self._build_pomodoro_menu(pomodoro_menu)
            menu.addMenu(pomodoro_menu)

        calendar_menu = QMenu("Calendar", menu)
        self._build_calendar_menu(calendar_menu)
        menu.addMenu(calendar_menu)

        integrations_menu = QMenu("Integrations", menu)
        self._build_integrations_menu(integrations_menu)
        menu.addMenu(integrations_menu)

        menu.addSeparator()

        behaviors_menu = QMenu("Behaviors", menu)
        self._build_behaviors_menu(behaviors_menu)
        menu.addMenu(behaviors_menu)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _build_pomodoro_menu(self, menu: QMenu):
        show_action = QAction("Show Timer", menu)
        show_action.triggered.connect(self._show_pomodoro)
        menu.addAction(show_action)

        start_action = QAction("Start Session", menu)
        start_action.triggered.connect(self._pomodoro_start)
        menu.addAction(start_action)

        skip_action = QAction("Skip", menu)
        skip_action.triggered.connect(self._pomodoro_skip)
        menu.addAction(skip_action)

    def _show_pomodoro(self):
        if self._pomodoro_widget:
            self._pomodoro_widget.show()
            self._pomodoro_widget.raise_()

    def _pomodoro_start(self):
        if self._pomodoro_widget:
            self._pomodoro_widget.integration.start_session()

    def _pomodoro_skip(self):
        if self._pomodoro_widget:
            self._pomodoro_widget.integration.skip()

    def _build_calendar_menu(self, menu: QMenu):
        calendar = self._integration_manager.get_integration("google_calendar")

        if calendar:
            next_event = calendar.get_next_event()
            if next_event:
                time_str = next_event.start_time.strftime("%I:%M %p").lstrip("0")
                info = QAction(f"Next: {next_event.summary} @ {time_str}", menu)
            else:
                info = QAction("No upcoming events", menu)
            info.setEnabled(False)
            menu.addAction(info)
        else:
            info = QAction("Not connected", menu)
            info.setEnabled(False)
            menu.addAction(info)

        menu.addSeparator()

        refresh_action = QAction("Refresh Now", menu)
        refresh_action.triggered.connect(self._calendar_refresh)
        menu.addAction(refresh_action)

    def _calendar_refresh(self):
        calendar = self._integration_manager.get_integration("google_calendar")
        if calendar:
            calendar.refresh()

    def _build_integrations_menu(self, menu: QMenu):
        integrations = self._integration_manager.list_integrations()

        if not integrations:
            no_integrations = QAction("No integrations loaded", menu)
            no_integrations.setEnabled(False)
            menu.addAction(no_integrations)
            return

        for name in integrations:
            # Skip pomodoro and calendar — they have their own dedicated submenus
            if name in ("pomodoro", "google_calendar"):
                continue
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

    def _build_behaviors_menu(self, menu: QMenu):
        if not self._behavior_registry:
            no_behaviors = QAction("No behaviors loaded", menu)
            no_behaviors.setEnabled(False)
            menu.addAction(no_behaviors)
            return

        for name in sorted(self._behavior_registry.list_behaviors()):
            display_name = name.replace("_", " ").title()
            action = QAction(display_name, menu)
            action.triggered.connect(lambda checked, n=name: self._trigger_behavior(n))
            menu.addAction(action)

    def _trigger_behavior(self, name: str):
        if self._behavior_registry:
            self._behavior_registry.trigger(name)

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

    def _show_dashboard(self, dashboard):
        dashboard.show()
        dashboard.raise_()
        dashboard.activateWindow()

    def _toggle_visibility(self):
        if self._pet_widget.isVisible():
            self._pet_widget.hide()
        else:
            self._pet_widget.show()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_visibility()

    def _open_settings(self):
        if self._panel_host is not None:
            self._panel_host.open_panel("settings")
        else:
            from src.ui.settings import SettingsDialog

            dialog = SettingsDialog(integration_manager=self._integration_manager)
            dialog.settings_changed.connect(self.settings_changed)
            dialog.exec()

    def _quit_app(self):
        from PyQt6.QtWidgets import QApplication, QMessageBox

        reply = QMessageBox.question(
            None,
            "Quit PIXEL",
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        async def _shutdown():
            await self._integration_manager.stop_all()
            QApplication.quit()

        try:
            loop = asyncio.get_event_loop()
            loop.create_task(_shutdown())
        except RuntimeError:
            QApplication.quit()
