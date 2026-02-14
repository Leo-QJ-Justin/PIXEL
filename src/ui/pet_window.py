import logging
import random
from datetime import datetime

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
    QUrl,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import QAction, QPainter, QPixmap
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import QInputDialog, QMenu, QMessageBox, QWidget

from config import get_behavior_settings, get_general_settings
from src.core.behavior_registry import BehaviorRegistry
from src.ui.speech_bubble import SpeechBubble

logger = logging.getLogger(__name__)


class PetWidget(QWidget):
    """Main desktop pet widget."""

    # Location flow signals (connected to GoogleCalendarIntegration)
    location_provided = pyqtSignal(str, str)  # (event_id, raw_address)
    location_confirmed = pyqtSignal(str)  # (event_id)
    location_rejected = pyqtSignal(str)  # (event_id)

    def __init__(self, behavior_registry: BehaviorRegistry):
        super().__init__()
        self._behavior_registry = behavior_registry
        self._drag_position = QPoint()
        self._system_move_pending = False
        self._is_alerting = False
        self._is_wandering = False
        self._is_sleeping = False
        self._facing_left = False
        self._last_activity_time = datetime.now()
        self._last_time_period: str | None = None
        self._active_weather_behavior: str | None = None

        # Location prompt state (Google Calendar integration)
        self._pending_location_request: dict | None = None

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

        # Speech bubble
        self._speech_bubble = SpeechBubble()
        self._speech_bubble_settings = get_general_settings().get("speech_bubble", {})

        # Time-period transition timer
        self._time_period_settings = get_behavior_settings("time_periods")
        self._time_period_timer = QTimer()
        self._time_period_timer.timeout.connect(self._check_time_period_transition)
        if self._time_period_settings.get("enabled", True):
            interval = self._time_period_settings.get("check_interval_ms", 30000)
            self._time_period_timer.start(interval)
            # Set initial period without triggering a transition
            self._last_time_period = self._get_current_period()

        # Connect to behavior registry signals
        self._behavior_registry.frame_changed.connect(self._on_frame_changed)
        self._behavior_registry.behavior_changed.connect(self._on_behavior_changed)

        self._setup_window()

        # Start with idle behavior, then play startup greeting
        self._behavior_registry.trigger("idle")
        self._play_startup_greeting()

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

    def _play_startup_greeting(self):
        """Play wave animation on app startup."""
        QTimer.singleShot(500, lambda: self._behavior_registry.trigger("wave"))

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

        # Reset activity timer on alerts (user interactions reset it separately)
        if behavior_name == "alert":
            self._last_activity_time = datetime.now()

        # Play sound if behavior has one
        sound_path = self._behavior_registry.current_sound_path
        if sound_path and sound_path.exists():
            self._alert_sound.setSource(QUrl.fromLocalFile(str(sound_path)))
            self._alert_sound.play()

        # Show greeting bubble on wave
        if behavior_name == "wave":
            wave_settings = get_behavior_settings("wave")
            self.show_bubble(wave_settings.get("greeting", "Hello!"))

        # Track active weather behavior
        if behavior_name in ("rainy", "sunny"):
            self._active_weather_behavior = behavior_name
        elif behavior_name == "idle" and context.get("condition"):
            # Weather integration triggered idle (weather cleared)
            self._active_weather_behavior = None

        # Show weather info bubble on rainy/sunny
        if behavior_name in ("rainy", "sunny"):
            description = context.get("description", behavior_name.capitalize())
            temperature = context.get("temperature", "")
            if temperature:
                self.show_bubble(f"{description}! {temperature}")
            else:
                self.show_bubble(f"{description}!")

        # Show speech bubble for Google Calendar alerts
        if behavior_name == "alert" and context.get("source") == "google_calendar":
            bubble_text = context.get("bubble_text", "Upcoming event!")
            self.show_bubble(bubble_text, duration_ms=5000)

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
        self._return_to_base_state()

    def _return_to_base_state(self):
        """Return to the active weather behavior if one is set, otherwise idle."""
        if self._active_weather_behavior:
            self._behavior_registry.trigger(
                self._active_weather_behavior, facing_left=self._facing_left
            )
        else:
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
        """Wake from sleep, reset activity timer, play wave greeting."""
        if not self._is_sleeping:
            return
        logger.info("Pet is waking up")
        self._is_sleeping = False
        self._last_activity_time = datetime.now()
        self._behavior_registry.trigger("wave")

    def show_bubble(self, text: str, duration_ms: int | None = None) -> None:
        """Show a speech bubble with the given text."""
        if not self._speech_bubble_settings.get("enabled", True):
            return
        if duration_ms is None:
            duration_ms = self._speech_bubble_settings.get("duration_ms", 3000)
        self._speech_bubble.update_position(self.pos(), self.size())
        self._speech_bubble.show_message(text, duration_ms)

    def _get_current_period(self) -> str | None:
        """Determine which time period the current time falls in."""
        periods = self._time_period_settings.get("periods", {})
        if not periods:
            return None

        now = datetime.now().strftime("%H:%M")

        # Sort periods by start time ascending
        sorted_periods = sorted(periods.items(), key=lambda item: item[1])

        # Find the last period whose start time <= current time
        current = sorted_periods[-1][0]  # Default to last (handles overnight wrap)
        for name, start_time in sorted_periods:
            if start_time <= now:
                current = name

        return current

    def _check_time_period_transition(self) -> None:
        """Check if the time period has changed and trigger behavior/greeting."""
        current_period = self._get_current_period()
        previous = self._last_time_period
        self._last_time_period = current_period

        # First check — just record, no trigger
        if previous is None:
            return

        # No change
        if current_period == previous:
            return

        # Skip trigger if pet is busy
        if self._is_alerting or self._is_sleeping or self._is_wandering:
            logger.debug(
                f"Time period changed to {current_period} but pet is busy, skipping trigger"
            )
            return

        logger.info(f"Time period transition: {previous} -> {current_period}")

        # Trigger the period behavior (silently fails if no behavior folder exists)
        if current_period:
            self._behavior_registry.trigger(current_period)

        # Show greeting bubble
        greeting = self._time_period_settings.get("greetings", {}).get(current_period)
        if greeting:
            self.show_bubble(greeting)

    def moveEvent(self, event):
        """Update speech bubble position when pet moves."""
        super().moveEvent(event)
        self._speech_bubble.update_position(self.pos(), self.size())

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
            self._system_move_pending = True
            self._last_activity_time = datetime.now()
            event.accept()

            # Wake up if sleeping
            if self._is_sleeping:
                self._wake_up()
                return

            # Dismiss alert on click
            if self._is_alerting:
                self.stop_alert()
                return

            # Handle pending location prompt on click
            if self._pending_location_request is not None:
                self._show_location_dialog()

    def mouseMoveEvent(self, event):
        """Handle dragging the widget."""
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._last_activity_time = datetime.now()
            if self._system_move_pending:
                self._system_move_pending = False
                window = self.windowHandle()
                if window and window.startSystemMove():
                    event.accept()
                    return
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Reset drag state on release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._system_move_pending = False
        super().mouseReleaseEvent(event)

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
        """Stop the alert and return to base state."""
        self._is_alerting = False
        self._bounce_animation.stop()
        self._behavior_registry.stop_current()
        self._return_to_base_state()

    # ── Notification & Location Flow ──────────────────────────────────

    @pyqtSlot(dict)
    def _on_notification(self, context: dict) -> None:
        """Handle bubble-only notification (no behavior change)."""
        bubble_text = context.get("bubble_text", "")
        if bubble_text:
            self.show_bubble(bubble_text, duration_ms=5000)

        if context.get("action") == "request_location":
            self._pending_location_request = context

    def _show_location_dialog(self) -> None:
        """Show dialog for user to input event location."""
        if self._pending_location_request is None:
            return

        event_id = self._pending_location_request.get("event_id", "")
        summary = self._pending_location_request.get("summary", "event")
        self._pending_location_request = None

        text, ok = QInputDialog.getText(
            self,
            "Add Location",
            f"Where is '{summary}'?",
        )
        if ok and text.strip():
            self.location_provided.emit(event_id, text.strip())
        else:
            self.location_rejected.emit(event_id)

    @pyqtSlot(str, str)
    def _on_address_confirmation(self, event_id: str, formatted_address: str) -> None:
        """Show confirmation dialog for geocoded address."""
        reply = QMessageBox.question(
            self,
            "Confirm Location",
            f"Did you mean:\n{formatted_address}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.location_confirmed.emit(event_id)
        else:
            self.location_rejected.emit(event_id)
