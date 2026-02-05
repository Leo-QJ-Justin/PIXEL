import logging
import random
from datetime import datetime

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer, QUrl, pyqtSlot
from PyQt6.QtGui import QAction, QPainter, QPixmap
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import QMenu, QWidget

from config import get_behavior_settings
from src.core.behavior_registry import BehaviorRegistry

logger = logging.getLogger(__name__)


class HaroWidget(QWidget):
    """Main Haro desktop pet widget."""

    def __init__(self, behavior_registry: BehaviorRegistry):
        super().__init__()
        self._behavior_registry = behavior_registry
        self._drag_position = QPoint()
        self._is_alerting = False
        self._is_wandering = False
        self._is_sleeping = False
        self._facing_left = False
        self._last_activity_time = datetime.now()

        # Current sprite to display
        self._current_sprite = QPixmap()

        # Sound effect for alerts
        self._alert_sound = QSoundEffect()

        # Bounce animation for alerts
        self._bounce_animation = QPropertyAnimation(self, b"pos")
        self._bounce_animation.setDuration(200)
        self._bounce_animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        self._bounce_animation.setLoopCount(10)

        # Movement animation for wandering
        self._move_animation = QPropertyAnimation(self, b"pos")
        self._move_animation.setDuration(1500)
        self._move_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._move_animation.finished.connect(self._on_wander_finished)

        # Wander decision timer
        wander_settings = get_behavior_settings("wander")
        wander_min = wander_settings.get("wander_interval_min_ms", 5000)
        wander_max = wander_settings.get("wander_interval_max_ms", 15000)
        self._wander_chance = wander_settings.get("wander_chance", 0.3)
        self._wander_min_ms = wander_min
        self._wander_max_ms = wander_max

        self._wander_timer = QTimer()
        self._wander_timer.timeout.connect(self._maybe_wander)
        self._wander_timer.start(random.randint(wander_min, wander_max))

        # Sleep check timer
        self._sleep_settings = get_behavior_settings("sleep")
        self._sleep_check_timer = QTimer()
        self._sleep_check_timer.timeout.connect(self._check_sleep_conditions)
        self._sleep_check_timer.start(5000)  # Check every 5 seconds

        # Connect to behavior registry signals
        self._behavior_registry.frame_changed.connect(self._on_frame_changed)
        self._behavior_registry.behavior_changed.connect(self._on_behavior_changed)

        self._setup_window()

        # Start with idle behavior
        self._behavior_registry.trigger("idle")

    def _setup_window(self):
        """Configure window properties for a desktop pet."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set initial size (will be updated when first sprite loads)
        self.setFixedSize(100, 100)

        # Position at bottom-right of screen
        self._move_to_default_position()

    def _move_to_default_position(self):
        """Move widget to bottom-right corner of screen."""
        screen = self.screen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.right() - self.width()
            y = geometry.bottom() - self.height()
            self.move(x, y)

    @pyqtSlot(QPixmap, bool)
    def _on_frame_changed(self, pixmap: QPixmap, facing_left: bool):
        """Handle frame change from behavior registry."""
        self._current_sprite = pixmap
        self._facing_left = facing_left

        # Update window size if needed
        if not pixmap.isNull():
            if pixmap.width() != self.width() or pixmap.height() != self.height():
                self.setFixedSize(pixmap.width(), pixmap.height())

        self.update()

    @pyqtSlot(str, dict)
    def _on_behavior_changed(self, behavior_name: str, context: dict):
        """Handle behavior change from registry."""
        logger.debug(f"Behavior changed to: {behavior_name}")

        # Track alerting state
        self._is_alerting = behavior_name == "alert"

        # Track wandering state
        if behavior_name == "wander":
            self._is_wandering = True
        elif behavior_name != "wander" and self._is_wandering:
            self._is_wandering = False

        # Track sleeping state
        if behavior_name == "sleep":
            self._is_sleeping = True
        elif behavior_name != "sleep" and self._is_sleeping:
            self._is_sleeping = False

        # Reset activity timer on non-idle, non-sleep behaviors
        if behavior_name in ("alert", "wander"):
            self._last_activity_time = datetime.now()

        # Play sound if behavior has one
        sound_path = self._behavior_registry.current_sound_path
        if sound_path and sound_path.exists():
            self._alert_sound.setSource(QUrl.fromLocalFile(str(sound_path)))
            self._alert_sound.play()

        # Start bounce animation for alert behavior
        if behavior_name == "alert":
            self._start_bounce()

    def _start_bounce(self):
        """Start the bounce animation for alerts."""
        start_pos = self.pos()
        bounce_pos = QPoint(start_pos.x(), start_pos.y() - 20)
        self._bounce_animation.setStartValue(bounce_pos)
        self._bounce_animation.setEndValue(start_pos)
        self._bounce_animation.start()

    def _maybe_wander(self):
        """Randomly decide to wander."""
        # Reset timer with random interval
        self._wander_timer.setInterval(random.randint(self._wander_min_ms, self._wander_max_ms))

        # Don't wander if alerting, already wandering, or sleeping
        if self._is_alerting or self._is_wandering or self._is_sleeping:
            return

        # Random chance to wander
        if random.random() < self._wander_chance:
            self._start_wander()

    def _start_wander(self):
        """Start wandering to a random position."""
        # Get screen bounds
        screen = self.screen()
        if not screen:
            return

        geo = screen.availableGeometry()

        # Pick random destination nearby (x-axis only)
        current_x = self.pos().x()
        move_distance = random.randint(50, 150) * random.choice([-1, 1])
        dest_x = current_x + move_distance

        # Clamp to screen bounds
        min_x = geo.left()
        max_x = geo.right() - self.width()
        dest_x = max(min_x, min(dest_x, max_x))

        dest_y = self.pos().y()

        # Set facing direction based on movement
        facing_left = dest_x < current_x

        # Trigger wander behavior
        self._behavior_registry.trigger("wander", facing_left=facing_left)

        # Start movement animation
        self._move_animation.setStartValue(self.pos())
        self._move_animation.setEndValue(QPoint(dest_x, dest_y))
        self._move_animation.start()

    def _on_wander_finished(self):
        """Handle wander movement completion."""
        self._is_wandering = False
        # Return to idle, keeping facing direction
        self._behavior_registry.trigger("idle", facing_left=self._facing_left)

    def _check_sleep_conditions(self):
        """Periodically check if the pet should sleep."""
        if self._is_sleeping or self._is_alerting or self._is_wandering:
            return

        # Check schedule first (if enabled)
        if self._sleep_settings.get("schedule_enabled", False):
            if self._is_scheduled_sleep_time():
                self._enter_sleep()
                return

        # Check inactivity timeout
        timeout_ms = self._sleep_settings.get("inactivity_timeout_ms", 60000)
        elapsed_ms = (datetime.now() - self._last_activity_time).total_seconds() * 1000
        if elapsed_ms >= timeout_ms:
            self._enter_sleep()

    def _is_scheduled_sleep_time(self) -> bool:
        """Check if current time falls within the sleep schedule."""
        start_str = self._sleep_settings.get("schedule_start", "22:00")
        end_str = self._sleep_settings.get("schedule_end", "06:00")

        now = datetime.now().strftime("%H:%M")

        # Handle overnight wrap (e.g., 22:00 -> 06:00)
        if start_str <= end_str:
            return start_str <= now < end_str
        else:
            return now >= start_str or now < end_str

    def _enter_sleep(self):
        """Trigger the sleep behavior."""
        logger.info("Pet is going to sleep")
        self._behavior_registry.trigger("sleep")

    def _wake_up(self):
        """Wake from sleep, reset activity timer, return to idle."""
        if not self._is_sleeping:
            return
        logger.info("Pet is waking up")
        self._is_sleeping = False
        self._last_activity_time = datetime.now()
        self._behavior_registry.stop_current()

    def paintEvent(self, event):
        """Draw the current sprite centered in the widget."""
        if self._current_sprite.isNull():
            return

        painter = QPainter(self)
        x = (self.width() - self._current_sprite.width()) // 2
        y = (self.height() - self._current_sprite.height()) // 2
        painter.drawPixmap(x, y, self._current_sprite)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging, alert dismissal, and waking."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._last_activity_time = datetime.now()
            event.accept()

            # Wake up if sleeping
            if self._is_sleeping:
                self._wake_up()
                return

            # Dismiss alert on click
            if self._is_alerting:
                self.stop_alert()

    def mouseMoveEvent(self, event):
        """Handle dragging the widget."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self._last_activity_time = datetime.now()
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        self._last_activity_time = datetime.now()
        if self._is_sleeping:
            self._wake_up()

        menu = QMenu(self)

        # Reset position action
        reset_action = QAction("Reset Position", self)
        reset_action.triggered.connect(self._move_to_default_position)
        menu.addAction(reset_action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        menu.exec(event.globalPos())

    def _quit_app(self):
        """Quit the application."""
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()

    @pyqtSlot(str)
    def trigger_alert(self, sender_name: str):
        """Trigger alert animation and sound (legacy interface for integrations)."""
        logger.debug(f"trigger_alert called for: {sender_name}")
        if self._is_alerting:
            logger.debug("Already alerting, skipping")
            return

        logger.info(f"Starting alert for: {sender_name}")

        # Stop any ongoing wander
        if self._is_wandering:
            self._move_animation.stop()
            self._is_wandering = False

        # Trigger alert through behavior registry
        self._behavior_registry.trigger("alert", {"sender": sender_name})

    def stop_alert(self):
        """Stop the alert and return to idle state."""
        self._is_alerting = False
        self._bounce_animation.stop()
        self._behavior_registry.stop_current()
