"""Behavior discovery, loading, and management."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QTransform

from config import get_sprite_default_facing

logger = logging.getLogger(__name__)


# Available characters and their sprite prefixes
CHARACTERS = {
    "haro": "",  # No prefix for Haro (default)
    "biru": "biru_",  # Biru sprites start with "biru_"
}



@dataclass
class Behavior:
    """Loaded behavior with sprites and config."""

    name: str
    sprites: list[QPixmap]
    sprites_flipped: list[QPixmap]
    frame_duration_ms: int
    loop: bool
    priority: int
    sound_path: Path | None
    can_be_interrupted: bool
    source: str = "core"  # "core" or integration name

    @classmethod
    def from_path(cls, path: Path, source: str = "core", character: str = "haro") -> "Behavior":
        """Load a behavior from a directory path."""
        name = path.name
        config_path = path / "config.json"

        # Load config
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
        else:
            config = {}

        frame_duration_ms = config.get("frame_duration_ms", 500)
        loop = config.get("loop", True)
        priority = config.get("priority", 0)
        can_be_interrupted = config.get("can_be_interrupted", True)
        sound_file = config.get("sound")

        # Get character sprite prefix
        prefix = CHARACTERS.get(character, "")

        # Load sprites matching the character prefix
        sprites_dir = path / "sprites"
        sprites = []
        if sprites_dir.exists():
            # Filter sprites by character prefix
            if prefix:
                # For non-default characters, match prefix (e.g., "biru_idle_1.png")
                pattern = f"{prefix}*.png"
            else:
                # For default character (haro), exclude files with other prefixes
                pattern = "*.png"

            sprite_files = sorted(sprites_dir.glob(pattern))

            # If using default character, filter out sprites with known prefixes
            if not prefix:
                other_prefixes = [p for p in CHARACTERS.values() if p]
                sprite_files = [
                    f for f in sprite_files if not any(f.name.startswith(p) for p in other_prefixes)
                ]

            for sprite_file in sprite_files:
                pixmap = QPixmap(str(sprite_file))
                if not pixmap.isNull():
                    sprites.append(pixmap)

        # Create flipped versions
        flip_transform = QTransform().scale(-1, 1)
        sprites_flipped = [sprite.transformed(flip_transform) for sprite in sprites]

        # Resolve sound path
        sound_path = None
        if sound_file:
            sounds_dir = path / "sounds"
            potential_path = sounds_dir / sound_file
            if potential_path.exists():
                sound_path = potential_path

        return cls(
            name=name,
            sprites=sprites,
            sprites_flipped=sprites_flipped,
            frame_duration_ms=frame_duration_ms,
            loop=loop,
            priority=priority,
            sound_path=sound_path,
            can_be_interrupted=can_be_interrupted,
            source=source,
        )


@dataclass
class BehaviorState:
    """Current behavior playback state."""

    behavior: Behavior
    frame_index: int = 0
    context: dict = field(default_factory=dict)
    facing_left: bool = False


class BehaviorRegistry(QObject):
    """
    Discovers, loads, and manages all behaviors.

    Behaviors are loaded from:
    1. behaviors/           (core behaviors)
    2. integrations/*/behaviors/  (integration-provided behaviors)
    """

    # Emitted when behavior changes: (behavior_name, context)
    behavior_changed = pyqtSignal(str, dict)

    # Emitted when frame advances: (pixmap, facing_left)
    frame_changed = pyqtSignal(QPixmap, bool)

    # Emitted when character changes: (character_name)
    character_changed = pyqtSignal(str)

    def __init__(self, character: str = "haro"):
        super().__init__()
        self._behaviors: dict[str, Behavior] = {}
        self._current_state: BehaviorState | None = None
        self._default_behavior: str = "idle"
        self._character: str = character

        # Store discovered paths for reloading on character change
        self._behavior_paths: list[tuple[Path, str]] = []  # (path, source)

        # Animation timer
        self._frame_timer = QTimer()
        self._frame_timer.timeout.connect(self._advance_frame)

    @property
    def character(self) -> str:
        """Current character name."""
        return self._character

    def set_character(self, character: str) -> None:
        """Switch to a different character and reload all behaviors."""
        if character not in CHARACTERS:
            logger.warning(f"Unknown character: {character}")
            return

        if character == self._character:
            return

        logger.info(f"Switching character from {self._character} to {character}")
        self._character = character

        # Stop current animation
        self._frame_timer.stop()
        self._current_state = None

        # Reload all behaviors with new character
        self._behaviors.clear()
        for path, source in self._behavior_paths:
            self._load_behaviors_from_path(path, source)

        # Emit signal and restart idle
        self.character_changed.emit(character)
        self.trigger(self._default_behavior)

    def discover_behaviors(self, paths: list[Path], source: str = "core") -> list[str]:
        """
        Scan paths for behavior folders and load them.

        Returns list of discovered behavior names.
        """
        discovered = []
        for base_path in paths:
            if not base_path.exists():
                continue

            # Store path for reloading on character change
            self._behavior_paths.append((base_path, source))
            discovered.extend(self._load_behaviors_from_path(base_path, source))

        return discovered

    def _load_behaviors_from_path(self, base_path: Path, source: str) -> list[str]:
        """Load behaviors from a single path."""
        discovered = []
        for behavior_path in base_path.iterdir():
            if not behavior_path.is_dir():
                continue

            # Skip if no sprites directory
            if not (behavior_path / "sprites").exists():
                continue

            behavior = Behavior.from_path(behavior_path, source=source, character=self._character)
            if behavior.sprites:
                self._behaviors[behavior.name] = behavior
                discovered.append(behavior.name)
                logger.info(
                    f"Loaded behavior: {behavior.name} (source: {source}, character: {self._character})"
                )

        return discovered

    def get_behavior(self, name: str) -> Behavior | None:
        """Get a loaded behavior by name."""
        return self._behaviors.get(name)

    def list_behaviors(self) -> list[str]:
        """Get list of all loaded behavior names."""
        return list(self._behaviors.keys())

    def trigger(
        self,
        name: str,
        context: dict | None = None,
        facing_left: bool | None = None,
    ) -> bool:
        """
        Trigger a behavior.

        Args:
            name: Behavior name to trigger
            context: Optional context dict
            facing_left: Optional facing direction (None = keep current)

        Returns:
            False if blocked by higher priority behavior.
        """
        behavior = self._behaviors.get(name)
        if not behavior:
            logger.warning(f"Behavior not found: {name}")
            return False

        # Check if current behavior blocks this one
        if self._current_state:
            current = self._current_state.behavior
            if not current.can_be_interrupted and current.priority >= behavior.priority:
                logger.debug(
                    f"Behavior {name} blocked by {current.name} (priority {current.priority})"
                )
                return False

        # Stop current animation
        self._frame_timer.stop()

        # Determine facing direction
        if facing_left is None:
            facing_left = self._current_state.facing_left if self._current_state else False

        # Set new state
        self._current_state = BehaviorState(
            behavior=behavior,
            frame_index=0,
            context=context or {},
            facing_left=facing_left,
        )

        # Emit change signal
        self.behavior_changed.emit(name, context or {})

        # Emit initial frame
        self._emit_current_frame()

        # Start animation timer if multiple frames
        if len(behavior.sprites) > 1:
            self._frame_timer.start(behavior.frame_duration_ms)

        logger.debug(f"Triggered behavior: {name}")
        return True

    def stop_current(self, force: bool = True) -> None:
        """Stop current behavior and return to default (idle).

        Args:
            force: If True, stop even non-interruptable behaviors.
        """
        self._frame_timer.stop()

        if force:
            # Clear current state to allow any behavior to take over
            self._current_state = None

        if self._default_behavior in self._behaviors:
            self.trigger(self._default_behavior)

    def set_facing(self, facing_left: bool) -> None:
        """Set the facing direction for the current behavior."""
        if self._current_state:
            self._current_state.facing_left = facing_left
            self._emit_current_frame()

    @property
    def current(self) -> str | None:
        """Name of currently playing behavior."""
        return self._current_state.behavior.name if self._current_state else None

    @property
    def current_behavior(self) -> Behavior | None:
        """Currently playing behavior object."""
        return self._current_state.behavior if self._current_state else None

    @property
    def current_sound_path(self) -> Path | None:
        """Sound path for current behavior, if any."""
        if self._current_state:
            return self._current_state.behavior.sound_path
        return None

    def _advance_frame(self) -> None:
        """Advance to next animation frame."""
        if not self._current_state:
            return

        state = self._current_state
        behavior = state.behavior
        num_frames = len(behavior.sprites)

        if num_frames == 0:
            return

        # Advance frame
        state.frame_index += 1

        # Check if animation complete
        if state.frame_index >= num_frames:
            if behavior.loop:
                state.frame_index = 0
            else:
                # Non-looping animation complete - return to default
                self._frame_timer.stop()
                self.stop_current()
                return

        self._emit_current_frame()

    def _emit_current_frame(self) -> None:
        """Emit the current frame pixmap."""
        if not self._current_state:
            return

        state = self._current_state
        behavior = state.behavior

        if not behavior.sprites:
            return

        frame_index = min(state.frame_index, len(behavior.sprites) - 1)

        # Determine if we need to flip based on default sprite orientation
        sprites_face_left = get_sprite_default_facing() == "left"
        need_flip = state.facing_left != sprites_face_left

        if need_flip:
            pixmap = behavior.sprites_flipped[frame_index]
        else:
            pixmap = behavior.sprites[frame_index]

        self.frame_changed.emit(pixmap, state.facing_left)
