"""Enum-based pet state machine replacing boolean flags."""

import logging
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class PetState(Enum):
    IDLE = auto()
    WANDERING = auto()
    SLEEPING = auto()
    ALERTING = auto()
    REACTING = auto()


# Valid transitions from each state
_TRANSITIONS: dict[PetState, set[PetState]] = {
    PetState.IDLE: {PetState.WANDERING, PetState.SLEEPING, PetState.ALERTING, PetState.REACTING},
    PetState.WANDERING: {PetState.IDLE, PetState.ALERTING},
    PetState.SLEEPING: {PetState.IDLE, PetState.ALERTING},
    PetState.ALERTING: {PetState.IDLE},
    PetState.REACTING: {PetState.IDLE, PetState.ALERTING},
}


class PetStateMachine(QObject):
    """Manages pet state transitions with validation."""

    state_changed = pyqtSignal(object, object)  # (old_state, new_state)

    def __init__(self, initial: PetState = PetState.IDLE):
        super().__init__()
        self._state = initial

    @property
    def state(self) -> PetState:
        return self._state

    def transition(self, new_state: PetState) -> bool:
        """Attempt a state transition. Returns True if successful."""
        if new_state == self._state:
            return True

        allowed = _TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            logger.debug(f"Blocked transition: {self._state.name} -> {new_state.name}")
            return False

        old = self._state
        self._state = new_state
        logger.debug(f"State transition: {old.name} -> {new_state.name}")
        self.state_changed.emit(old, new_state)
        return True

    def force(self, new_state: PetState) -> None:
        """Force a state transition regardless of rules."""
        old = self._state
        self._state = new_state
        if old != new_state:
            logger.debug(f"Forced transition: {old.name} -> {new_state.name}")
            self.state_changed.emit(old, new_state)

    @property
    def is_idle(self) -> bool:
        return self._state == PetState.IDLE

    @property
    def is_busy(self) -> bool:
        return self._state in (
            PetState.ALERTING,
            PetState.WANDERING,
            PetState.SLEEPING,
            PetState.REACTING,
        )
