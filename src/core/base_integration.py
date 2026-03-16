"""Abstract base class for all integrations."""

from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal


class QObjectABCMeta(type(QObject), ABCMeta):
    """Metaclass that combines QObject and ABC metaclasses."""

    pass


class BaseIntegration(QObject, metaclass=QObjectABCMeta):
    """
    Abstract base class for all integrations.

    Integrations connect to external services and trigger behaviors.
    They can optionally provide custom behaviors with their own sprites.
    """

    # Signal to request a behavior trigger
    request_behavior = pyqtSignal(str, dict)  # (behavior_name, context)

    # Signal to stop the current behavior and return to default
    request_stop_behavior = pyqtSignal()

    # Signal for bubble-only notifications (bypasses behavior system)
    request_notification = pyqtSignal(dict)  # context dict with bubble_text, etc.

    def __init__(self, integration_path: Path, settings: dict[str, Any]):
        super().__init__()
        self._path = integration_path
        # Merge: integration defaults first, then saved settings override
        self._settings = {**self.get_default_settings(), **settings}
        self._enabled = self._settings.get("enabled", True)

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier (e.g., 'weather')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'Weather')."""
        pass

    @property
    def behaviors_path(self) -> Path | None:
        """Path to integration's behaviors folder, if any."""
        path = self._path / "behaviors"
        return path if path.exists() else None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @property
    def settings(self) -> dict[str, Any]:
        """Get the integration settings."""
        return self._settings

    def get_default_settings(self) -> dict[str, Any]:
        """Default settings for this integration."""
        return {"enabled": True}

    @abstractmethod
    async def start(self) -> None:
        """Start the integration (connect to service, begin listening)."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the integration and clean up."""
        pass

    def trigger(self, behavior_name: str, context: dict | None = None) -> None:
        """Request a behavior to be triggered."""
        self.request_behavior.emit(behavior_name, context or {})

    def stop_behavior(self) -> None:
        """Stop the current behavior and return to default."""
        self.request_stop_behavior.emit()

    def notify(self, context: dict) -> None:
        """Send a bubble-only notification (no behavior change)."""
        self.request_notification.emit(context)

    def setup_ui(self, pet_widget) -> None:
        """Optional hook for integrations to wire their own UI signals.

        Called once after the integration is loaded and the pet widget exists.
        Override this to connect integration-specific signals to the pet widget.
        """
        pass

    def build_dashboard(self):
        """Return a DashboardHost window, or None if no dashboard.

        Override in subclasses that provide a dashboard UI.
        """
        return None
