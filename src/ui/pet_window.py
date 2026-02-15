import logging
import os
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
from PyQt6.QtWidgets import QMenu, QWidget

from config import get_behavior_settings, get_general_settings, load_settings
from src.core.behavior_registry import BehaviorRegistry
from src.ui.speech_bubble import SpeechBubble

logger = logging.getLogger(__name__)


class PetWidget(QWidget):
    """Main desktop pet widget."""

    # Route confirmation signals (smart origin detection)
    route_submitted = pyqtSignal(str, str, str, str)  # (event_id, origin, destination, mode)
    route_confirmed = pyqtSignal(str)  # (event_id)
    route_rejected = pyqtSignal(str)  # (event_id)
    route_skipped = pyqtSignal(str)  # (event_id)

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

        # Route prompt state (smart origin detection)
        self._pending_route_request: dict | None = None

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

    def _get_display_name(self) -> str:
        """Return the user's display name from settings, falling back to system username."""
        name = load_settings().get("user_name", "")
        if name:
            return name
        try:
            return os.getlogin()
        except OSError:
            return ""

    def _personalize_greeting(self, greeting: str) -> str:
        """Insert the user's name into a greeting (e.g. 'Hello!' -> 'Hello, Leo!')."""
        name = self._get_display_name()
        if not name or "!" not in greeting:
            return greeting
        return greeting.replace("!", f", {name}!", 1)

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
            greeting = wave_settings.get("greeting", "Hello!")
            self.show_bubble(self._personalize_greeting(greeting))

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
            self.show_bubble(self._personalize_greeting(greeting))

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

            # Handle pending route prompt on click
            if self._pending_route_request is not None:
                self._show_route_dialog()

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

    # ── Notification & Route Flow ───────────────────────────────────

    @pyqtSlot(dict)
    def _on_notification(self, context: dict) -> None:
        """Handle bubble-only notification (no behavior change)."""
        bubble_text = context.get("bubble_text", "")
        if bubble_text:
            self.show_bubble(bubble_text, duration_ms=5000)

        if context.get("action") == "request_route":
            self._pending_route_request = context

    # ── Route Confirmation Flow (smart origin detection) ─────────────

    _MODE_LABELS = {
        "DRIVE": "Driving",
        "TRANSIT": "Transit",
        "WALK": "Walking",
        "BICYCLE": "Cycling",
    }

    def _show_route_dialog(self) -> None:
        """Show dialog for user to input origin, destination, and travel mode."""
        if self._pending_route_request is None:
            return

        event_id = self._pending_route_request.get("event_id", "")
        summary = self._pending_route_request.get("summary", "event")
        origin = self._pending_route_request.get("origin", "")
        destination = self._pending_route_request.get("destination", "")
        travel_modes = self._pending_route_request.get("travel_modes", ["DRIVE"])
        self._pending_route_request = None

        from PyQt6.QtWidgets import (
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QLineEdit,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle(f'Route for "{summary}"')
        layout = QFormLayout(dialog)

        origin_edit = QLineEdit(origin, dialog)
        origin_edit.setPlaceholderText("Enter starting location")
        layout.addRow("From:", origin_edit)

        dest_edit = QLineEdit(destination, dialog)
        dest_edit.setPlaceholderText("Enter destination")
        layout.addRow("To:", dest_edit)

        mode_combo = QComboBox(dialog)
        for mode in travel_modes:
            mode_combo.addItem(self._MODE_LABELS.get(mode, mode), mode)
        layout.addRow("Travel by:", mode_combo)

        buttons = QDialogButtonBox(dialog)
        confirm_btn = buttons.addButton("Confirm", QDialogButtonBox.ButtonRole.AcceptRole)
        skip_btn = buttons.addButton("Skip", QDialogButtonBox.ButtonRole.RejectRole)
        layout.addRow(buttons)

        confirm_btn.clicked.connect(dialog.accept)
        skip_btn.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            from_text = origin_edit.text().strip()
            to_text = dest_edit.text().strip()
            selected_mode = mode_combo.currentData()
            if from_text and to_text:
                self.route_submitted.emit(event_id, from_text, to_text, selected_mode)
            else:
                self.show_bubble("Both From and To are required.")
                self.route_skipped.emit(event_id)
        else:
            self.route_skipped.emit(event_id)

    @pyqtSlot(str, str, str, str)
    def _on_route_verification(
        self, event_id: str, geocoded_origin: str, geocoded_destination: str, mode: str
    ) -> None:
        """Show verification dialog for geocoded route."""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

        mode_label = self._MODE_LABELS.get(mode, mode)

        dialog = QDialog(self)
        dialog.setWindowTitle("Confirm route")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"From: {geocoded_origin}"))
        layout.addWidget(QLabel(f"To: {geocoded_destination}"))
        layout.addWidget(QLabel(f"Travel by: {mode_label}"))

        buttons = QDialogButtonBox(dialog)
        looks_good = buttons.addButton("Looks good", QDialogButtonBox.ButtonRole.AcceptRole)
        no_edit = buttons.addButton("No, edit", QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(buttons)

        looks_good.clicked.connect(dialog.accept)
        no_edit.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.route_confirmed.emit(event_id)
        else:
            self.route_rejected.emit(event_id)
