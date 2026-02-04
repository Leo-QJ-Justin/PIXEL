"""Core module for Haro Desktop Pet."""

from src.core.base_integration import BaseIntegration
from src.core.behavior_registry import Behavior, BehaviorRegistry, BehaviorState
from src.core.integration_manager import IntegrationManager

__all__ = [
    "BaseIntegration",
    "Behavior",
    "BehaviorRegistry",
    "BehaviorState",
    "IntegrationManager",
]
