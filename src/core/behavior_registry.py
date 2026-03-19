"""Behavior discovery, loading, and management using GIF-based animation."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QMovie, QPixmap, QTransform

logger = logging.getLogger(__name__)


@dataclass
class Behavior:
    """Loaded behavior with GIF animation."""

    name: str
    gif_path: Path
    priority: int
    can_be_interrupted: bool
    loop: bool
    sound_path: Path | None
    source: str = "core"

    @classmethod
    def from_path(cls, path: Path, source: str = "core") -> "Behavior | None":
        """Load a behavior from a directory path. Returns None if no sprites found."""
        name = path.name
        config_path = path / "config.json"

        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
        else:
            config = {}

        priority = config.get("priority", 0)
        can_be_interrupted = config.get("can_be_interrupted", True)
        loop = config.get("loop", True)
        sound_file = config.get("sound")

        media_dir = path / "media"
        if not media_dir.exists():
            return None

        # Prefer GIF, fall back to legacy PNG conversion
        gif_files = sorted(media_dir.glob("*.gif"))
        if gif_files:
            gif_path = gif_files[0]
        else:
            png_files = sorted(media_dir.glob("*.png"))
            if not png_files:
                return None

            from src.utils.sprite_tools import pngs_to_gif

            frame_duration_ms = config.get("frame_duration_ms", 500)
            gif_path = media_dir / f"{name}.gif"
            try:
                pngs_to_gif(png_files, gif_path, frame_duration_ms, loop)
                logger.info(f"Converted {len(png_files)} PNGs to GIF: {gif_path}")
            except Exception:
                logger.exception(f"Failed to convert PNGs to GIF for {name}")
                return None

        # Resolve sound
        sound_path = None
        if sound_file:
            potential = path / "sounds" / sound_file
            if potential.exists():
                sound_path = potential

        return cls(
            name=name,
            gif_path=gif_path,
            priority=priority,
            can_be_interrupted=can_be_interrupted,
            loop=loop,
            sound_path=sound_path,
            source=source,
        )


@dataclass
class BehaviorState:
    """Current behavior playback state."""

    behavior: Behavior
    facing_left: bool = False
    context: dict = field(default_factory=dict)


class BehaviorRegistry(QObject):
    """
    Discovers, loads, and manages GIF-based behaviors.

    Uses QMovie for native GIF playback instead of manual frame cycling.
    """

    behavior_changed = pyqtSignal(str, dict)
    frame_changed = pyqtSignal(QPixmap, bool)

    def __init__(self, sprites_face_left: bool = False):
        super().__init__()
        self._behaviors: dict[str, Behavior] = {}
        self._current_state: BehaviorState | None = None
        self._movie: QMovie | None = None
        self._default_behavior: str = "idle"
        self._sprites_face_left = sprites_face_left

    def discover_behaviors(self, paths: list[Path], source: str = "core") -> list[str]:
        """Scan paths for behavior folders and load them."""
        discovered = []
        for base_path in paths:
            if not base_path.exists():
                continue
            for behavior_path in base_path.iterdir():
                if not behavior_path.is_dir():
                    continue
                if not (behavior_path / "media").exists():
                    continue
                behavior = Behavior.from_path(behavior_path, source=source)
                if behavior:
                    self._behaviors[behavior.name] = behavior
                    discovered.append(behavior.name)
                    logger.info(f"Loaded behavior: {behavior.name} (source: {source})")
        return discovered

    def get_behavior(self, name: str) -> Behavior | None:
        return self._behaviors.get(name)

    def list_behaviors(self) -> list[str]:
        return list(self._behaviors.keys())

    def trigger(
        self,
        name: str,
        context: dict | None = None,
        facing_left: bool | None = None,
    ) -> bool:
        """Trigger a behavior. Returns False if blocked by higher priority."""
        behavior = self._behaviors.get(name)
        if not behavior:
            logger.warning(f"Behavior not found: {name}")
            return False

        if self._current_state:
            current = self._current_state.behavior
            if not current.can_be_interrupted and current.priority >= behavior.priority:
                return False

        self._stop_movie()

        if facing_left is None:
            facing_left = self._current_state.facing_left if self._current_state else False

        self._current_state = BehaviorState(
            behavior=behavior,
            facing_left=facing_left,
            context=context or {},
        )

        self.behavior_changed.emit(name, context or {})

        # Start QMovie for the GIF
        self._movie = QMovie(str(behavior.gif_path))
        self._movie.frameChanged.connect(self._on_frame_changed)
        self._movie.start()

        # Emit initial frame
        self._emit_current_frame()

        logger.debug(f"Triggered behavior: {name}")
        return True

    def stop_current(self, force: bool = True) -> None:
        """Stop current behavior and return to default."""
        self._stop_movie()

        if force:
            self._current_state = None

        if self._default_behavior in self._behaviors:
            self.trigger(self._default_behavior)

    def set_facing(self, facing_left: bool) -> None:
        if self._current_state:
            self._current_state.facing_left = facing_left
            self._emit_current_frame()

    @property
    def current(self) -> str | None:
        return self._current_state.behavior.name if self._current_state else None

    @property
    def current_behavior(self) -> Behavior | None:
        return self._current_state.behavior if self._current_state else None

    @property
    def current_sound_path(self) -> Path | None:
        if self._current_state:
            return self._current_state.behavior.sound_path
        return None

    def _stop_movie(self) -> None:
        if self._movie:
            self._movie.stop()
            self._movie.frameChanged.disconnect(self._on_frame_changed)
            self._movie.deleteLater()
            self._movie = None

    def _on_frame_changed(self, frame_number: int) -> None:
        """Handle QMovie frame advancement."""
        if not self._current_state or not self._movie:
            return

        self._emit_current_frame()

        # For non-looping behaviors, stop after the last frame
        if not self._current_state.behavior.loop:
            frame_count = self._movie.frameCount()
            if frame_count > 0 and frame_number >= frame_count - 1:
                self._movie.stop()
                QTimer.singleShot(0, self.stop_current)

    def _emit_current_frame(self) -> None:
        """Emit the current frame pixmap, flipped if needed."""
        if not self._current_state or not self._movie:
            return

        pixmap = self._movie.currentPixmap()
        if pixmap.isNull():
            return

        need_flip = self._current_state.facing_left != self._sprites_face_left

        if need_flip:
            pixmap = pixmap.transformed(QTransform().scale(-1, 1))

        self.frame_changed.emit(pixmap, self._current_state.facing_left)
