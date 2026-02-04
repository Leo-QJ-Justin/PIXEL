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

    def __init__(self, integration_path: Path, settings: dict[str, Any]):
        super().__init__()
        self._path = integration_path
        self._settings = settings
        self._enabled = settings.get("enabled", True)

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier (e.g., 'telegram')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'Telegram Notifications')."""
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
