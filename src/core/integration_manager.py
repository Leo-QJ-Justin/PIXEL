"""Integration discovery, loading, and lifecycle management."""

import importlib.util
import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from src.core.base_integration import BaseIntegration
from src.core.behavior_registry import BehaviorRegistry

logger = logging.getLogger(__name__)


class IntegrationManager(QObject):
    """
    Discovers, loads, and manages integrations.

    Responsibilities:
    - Scan integrations/ directory for integration.py files
    - Load and instantiate integration classes
    - Connect integration signals to BehaviorRegistry
    - Manage integration lifecycle (start/stop)
    """

    integration_loaded = pyqtSignal(str)
    integration_unloaded = pyqtSignal(str)
    integration_started = pyqtSignal(str)
    integration_stopped = pyqtSignal(str)
    notification_requested = pyqtSignal(dict)

    def __init__(
        self,
        integrations_path: Path,
        behavior_registry: BehaviorRegistry,
        settings: dict[str, Any],
    ):
        super().__init__()
        self._integrations_path = integrations_path
        self._behavior_registry = behavior_registry
        self._settings = settings

        self._integrations: dict[str, BaseIntegration] = {}
        self._running: set[str] = set()
        self._dashboards: dict[str, object] = {}

    def discover(self) -> list[str]:
        """
        Find all integrations in the integrations/ directory.

        Returns list of discovered integration names.
        """
        discovered = []

        if not self._integrations_path.exists():
            logger.warning(f"Integrations path does not exist: {self._integrations_path}")
            return discovered

        for item in self._integrations_path.iterdir():
            if not item.is_dir():
                continue

            integration_file = item / "integration.py"
            if integration_file.exists():
                discovered.append(item.name)
                logger.debug(f"Discovered integration: {item.name}")

        return discovered

    def load(self, name: str) -> BaseIntegration | None:
        """
        Load an integration by name.

        Returns the integration instance or None if loading failed.
        """
        if name in self._integrations:
            return self._integrations[name]

        integration_path = self._integrations_path / name
        integration_file = integration_path / "integration.py"

        if not integration_file.exists():
            logger.error(f"Integration file not found: {integration_file}")
            return None

        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(
                f"integrations.{name}.integration", integration_file
            )
            if spec is None or spec.loader is None:
                logger.error(f"Could not load integration spec: {name}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the integration class (subclass of BaseIntegration)
            integration_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseIntegration)
                    and attr is not BaseIntegration
                ):
                    integration_class = attr
                    break

            if integration_class is None:
                logger.error(f"No BaseIntegration subclass found in {integration_file}")
                return None

            # Get integration settings
            integration_settings = self._settings.get("integrations", {}).get(name, {})

            # Instantiate
            integration = integration_class(integration_path, integration_settings)

            # Connect signals
            integration.request_behavior.connect(self._on_behavior_requested)
            integration.request_notification.connect(self._on_notification_requested)

            # Load integration-specific behaviors if any
            if integration.behaviors_path:
                self._behavior_registry.discover_behaviors(
                    [integration.behaviors_path], source=name
                )

            self._integrations[name] = integration
            self.integration_loaded.emit(name)
            logger.info(f"Loaded integration: {integration.display_name}")

            # Build dashboard if integration provides one
            dashboard = integration.build_dashboard()
            if dashboard is not None:
                self._dashboards[name] = dashboard

            return integration

        except Exception as e:
            logger.exception(f"Failed to load integration {name}: {e}")
            return None

    def unload(self, name: str) -> bool:
        """Unload an integration."""
        if name not in self._integrations:
            return False

        # Stop if running
        if name in self._running:
            # Note: This should be awaited in async context
            logger.warning(f"Integration {name} is running, stopping...")
            self._running.discard(name)

        self._dashboards.pop(name, None)
        del self._integrations[name]
        self.integration_unloaded.emit(name)
        logger.info(f"Unloaded integration: {name}")
        return True

    def get_integration(self, name: str) -> BaseIntegration | None:
        """Get a loaded integration by name."""
        return self._integrations.get(name)

    def get_dashboards(self) -> dict:
        """Get all registered dashboards keyed by integration name."""
        return dict(self._dashboards)

    def list_integrations(self) -> list[str]:
        """Get list of all loaded integration names."""
        return list(self._integrations.keys())

    def is_running(self, name: str) -> bool:
        """Check if an integration is currently running."""
        return name in self._running

    async def start(self, name: str) -> bool:
        """Start an integration."""
        integration = self._integrations.get(name)
        if not integration:
            logger.error(f"Integration not loaded: {name}")
            return False

        if name in self._running:
            logger.warning(f"Integration already running: {name}")
            return True

        try:
            await integration.start()
            self._running.add(name)
            self.integration_started.emit(name)
            logger.info(f"Started integration: {integration.display_name}")
            return True
        except Exception as e:
            logger.exception(f"Failed to start integration {name}: {e}")
            return False

    async def stop(self, name: str) -> bool:
        """Stop an integration."""
        integration = self._integrations.get(name)
        if not integration:
            return False

        if name not in self._running:
            return True

        try:
            await integration.stop()
            self._running.discard(name)
            self.integration_stopped.emit(name)
            logger.info(f"Stopped integration: {integration.display_name}")
            return True
        except Exception as e:
            logger.exception(f"Failed to stop integration {name}: {e}")
            return False

    def setup_all_ui(self, pet_widget) -> None:
        """Call setup_ui on all loaded integrations."""
        for name, integration in self._integrations.items():
            try:
                integration.setup_ui(pet_widget)
            except Exception:
                logger.exception(f"Failed to setup UI for integration {name}")

    async def start_all_enabled(self) -> None:
        """Start all enabled integrations."""
        for name, integration in self._integrations.items():
            if integration.enabled:
                await self.start(name)

    async def stop_all(self) -> None:
        """Stop all running integrations."""
        for name in list(self._running):
            await self.stop(name)

    def _on_behavior_requested(self, behavior_name: str, context: dict) -> None:
        """Handle behavior request from an integration."""
        logger.debug(f"Behavior requested: {behavior_name} with context {context}")
        self._behavior_registry.trigger(behavior_name, context)

    def _on_notification_requested(self, context: dict) -> None:
        """Forward bubble-only notification from an integration."""
        logger.debug(f"Notification requested: {context}")
        self.notification_requested.emit(context)
