"""Core module for desktop pet."""

from src.core.base_integration import BaseIntegration
from src.core.behavior_registry import Behavior, BehaviorRegistry, BehaviorState
from src.core.integration_manager import IntegrationManager
from src.core.pet_state import PetState, PetStateMachine

__all__ = [
    "BaseIntegration",
    "Behavior",
    "BehaviorRegistry",
    "BehaviorState",
    "IntegrationManager",
    "PetState",
    "PetStateMachine",
]
