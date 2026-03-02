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
from PyQt6.QtWidgets import QMenu, QWidget

from config import load_settings
from src.core.behavior_registry import BehaviorRegistry
from src.core.pet_state import PetState, PetStateMachine
from src.ui.speech_bubble import SpeechBubble

logger = logging.getLogger(__name__)


class RandomIntervalTimer(QTimer):
    """QTimer that re-randomizes its interval on each tick."""

    def __init__(self, min_ms: int, max_ms: int, parent=None):
        super().__init__(parent)
        self._min_ms = min_ms
        self._max_ms = max_ms
        self.timeout.connect(self._rerandomize)

    def _rerandomize(self):
        self.setInterval(random.randint(self._min_ms, self._max_ms))

    def start_random(self):
        self.start(random.randint(self._min_ms, self._max_ms))


class PetWidget(QWidget):
    """Main desktop pet widget."""

    clicked = pyqtSignal()

    def __init__(self, behavior_registry: BehaviorRegistry):
        super().__init__()
        self._behavior_registry = behavior_registry
        self._state_machine = PetStateMachine()
        self._current_sprite = QPixmap()

        # Load all settings once
        settings = load_settings()
        self._behavior_settings = settings.get("behaviors", {})
        self._general_settings = settings.get("general", {})

        self._init_interaction_state()
        self._init_animations()
        self._init_timers()
        self._init_speech_bubble()
        self._connect_signals()
        self._setup_window()

        self._behavior_registry.trigger("idle")
        self._play_startup_greeting()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------

    def _init_interaction_state(self):
        """Set up drag, tap, facing, and activity tracking state."""
        self._drag_position = QPoint()
        self._tap_origin = None
        self._system_move_pending = False
        self._facing_left = False
        self._initial_position_set = False
        self._last_activity_time = datetime.now()
        self._last_time_period: str | None = None
        self._notification_callback = None

    def _init_animations(self):
        """Set up move and bounce animations. Sound is lazy-created."""
        self._alert_sound = None  # lazy-created on first use

        self._bounce_animation = QPropertyAnimation(self, b"pos")
        self._bounce_animation.setDuration(200)
        self._bounce_animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        self._bounce_animation.setLoopCount(10)

        self._move_animation = QPropertyAnimation(self, b"pos")
        self._move_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._move_animation.finished.connect(self._on_wander_finished)

    def _init_timers(self):
        """Set up wander, idle variety, sleep, and time-period timers."""
        wander = self._behavior_settings.get("wander", {})
        self._wander_chance = wander.get("wander_chance", 0.3)
        self._wander_timer = RandomIntervalTimer(
            wander.get("wander_interval_min_ms", 5000),
            wander.get("wander_interval_max_ms", 15000),
        )
        self._wander_timer.timeout.connect(self._maybe_wander)
        self._wander_timer.start_random()

        idle_variety = self._behavior_settings.get("idle_variety", {})
        self._idle_variety_enabled = idle_variety.get("enabled", True)
        self._idle_variety_behaviors = idle_variety.get("behaviors", ["look_around", "yawn"])
        self._idle_variety_chance = idle_variety.get("chance", 0.4)
        self._idle_variety_timer = RandomIntervalTimer(
            idle_variety.get("interval_min_ms", 20000),
            idle_variety.get("interval_max_ms", 60000),
        )
        self._idle_variety_timer.timeout.connect(self._maybe_idle_variety)
        if self._idle_variety_enabled:
            self._idle_variety_timer.start_random()

        self._sleep_settings = self._behavior_settings.get("sleep", {})
        self._sleep_check_timer = QTimer()
        self._sleep_check_timer.timeout.connect(self._check_sleep_conditions)
        self._sleep_check_timer.start(5000)

        self._time_period_settings = self._behavior_settings.get("time_periods", {})
        self._time_period_timer = QTimer()
        self._time_period_timer.timeout.connect(self._check_time_period_transition)
        if self._time_period_settings.get("enabled", True):
            interval = self._time_period_settings.get("check_interval_ms", 30000)
            self._time_period_timer.start(interval)
            self._last_time_period = self._get_current_period()

    def _init_speech_bubble(self):
        """Set up speech bubble widget and its settings."""
        self._speech_bubble = SpeechBubble()
        self._speech_bubble_settings = self._general_settings.get("speech_bubble", {})

    def _connect_signals(self):
        """Wire up all signal connections."""
        self._behavior_registry.frame_changed.connect(self._on_frame_changed)
        self._behavior_registry.behavior_changed.connect(self._on_behavior_changed)
        self.clicked.connect(self._on_clicked)

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(100, 100)
        self._move_to_default_position()

    def _play_startup_greeting(self):
        QTimer.singleShot(500, lambda: self._behavior_registry.trigger("wave"))

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------

    def _get_display_name(self) -> str:
        name = load_settings().get("user_name", "")
        if name:
            return name
        try:
            return os.getlogin()
        except OSError:
            return ""

    def _personalize_greeting(self, greeting: str) -> str:
        name = self._get_display_name()
        if not name or "!" not in greeting:
            return greeting
        return greeting.replace("!", f", {name}!", 1)

    # ------------------------------------------------------------------
    # Positioning
    # ------------------------------------------------------------------

    def _move_to_default_position(self):
        screen = self.screen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.right() - self.width()
            y = geometry.bottom() - self.height()
            self.move(x, y)

    # ------------------------------------------------------------------
    # Frame & behavior callbacks
    # ------------------------------------------------------------------

    @pyqtSlot(QPixmap, bool)
    def _on_frame_changed(self, pixmap: QPixmap, facing_left: bool):
        self._current_sprite = pixmap
        self._facing_left = facing_left

        if not pixmap.isNull():
            if pixmap.width() != self.width() or pixmap.height() != self.height():
                self.setFixedSize(pixmap.width(), pixmap.height())
                if not self._initial_position_set:
                    self._initial_position_set = True
                    self._move_to_default_position()

        self.update()

    @pyqtSlot(str, dict)
    def _on_behavior_changed(self, behavior_name: str, context: dict):
        logger.debug(f"Behavior changed to: {behavior_name}")

        if behavior_name == "alert":
            self._last_activity_time = datetime.now()

        self._handle_behavior_sound()
        self._handle_behavior_greeting(behavior_name, context)

        if behavior_name == "alert":
            self._start_bounce()

        # Return to IDLE when a REACTING behavior finishes (flinch, idle variety, etc.)
        if behavior_name == "idle" and self._state_machine.state == PetState.REACTING:
            self._state_machine.force(PetState.IDLE)

    def _handle_behavior_sound(self):
        """Play sound if the current behavior has one."""
        sound_path = self._behavior_registry.current_sound_path
        if not sound_path or not sound_path.exists():
            return

        if self._alert_sound is None:
            from PyQt6.QtMultimedia import QSoundEffect

            self._alert_sound = QSoundEffect()

        self._alert_sound.setSource(QUrl.fromLocalFile(str(sound_path)))
        self._alert_sound.play()

    def _handle_behavior_greeting(self, behavior_name: str, context: dict):
        """Show speech bubble for wave greetings or integration context text."""
        if behavior_name == "wave":
            wave_settings = self._behavior_settings.get("wave", {})
            greeting = wave_settings.get("greeting", "Hello!")
            self.show_bubble(self._personalize_greeting(greeting))

        bubble_text = context.get("bubble_text")
        if bubble_text:
            self.show_bubble(bubble_text, duration_ms=context.get("bubble_duration_ms", 5000))

    # ------------------------------------------------------------------
    # Click reaction
    # ------------------------------------------------------------------

    def _on_clicked(self):
        """Handle click/tap — trigger a flinch reaction if idle."""
        if not self._state_machine.is_idle:
            return
        if not self._state_machine.transition(PetState.REACTING):
            return
        self._last_activity_time = datetime.now()
        self._behavior_registry.trigger("flinch")

    # ------------------------------------------------------------------
    # Idle variety
    # ------------------------------------------------------------------

    def _maybe_idle_variety(self):
        """Occasionally trigger a random idle-like behavior for variety."""
        if not self._state_machine.is_idle:
            return

        if random.random() >= self._idle_variety_chance:
            return

        # Pick a random idle variety behavior that is actually loaded
        available = [
            b
            for b in self._idle_variety_behaviors
            if self._behavior_registry.get_behavior(b) is not None
        ]
        if not available:
            return

        if not self._state_machine.transition(PetState.REACTING):
            return

        self._behavior_registry.trigger(random.choice(available))

    # ------------------------------------------------------------------
    # Alert bounce
    # ------------------------------------------------------------------

    def _start_bounce(self):
        start_pos = self.pos()
        bounce_pos = QPoint(start_pos.x(), start_pos.y() - 20)
        self._bounce_animation.setStartValue(bounce_pos)
        self._bounce_animation.setEndValue(start_pos)
        self._bounce_animation.start()

    # ------------------------------------------------------------------
    # Wander
    # ------------------------------------------------------------------

    def _maybe_wander(self):
        if self._state_machine.is_busy:
            return

        if random.random() < self._wander_chance:
            self._start_wander()

    def _start_wander(self):
        screen = self.screen()
        if not screen:
            return

        if not self._state_machine.transition(PetState.WANDERING):
            return

        geo = screen.availableGeometry()

        current_x = self.pos().x()
        move_distance = random.randint(50, 150) * random.choice([-1, 1])
        dest_x = max(geo.left(), min(current_x + move_distance, geo.right() - self.width()))
        dest_y = self.pos().y()

        distance = abs(dest_x - current_x)
        facing_left = dest_x < current_x

        self._behavior_registry.trigger("wander", facing_left=facing_left)

        # Scale duration to distance: ~15ms per pixel, clamped to 750-2500ms
        duration = max(750, min(int(distance * 15), 2500))
        self._move_animation.setDuration(duration)
        self._move_animation.setStartValue(self.pos())
        self._move_animation.setEndValue(QPoint(dest_x, dest_y))
        self._move_animation.start()

    def _on_wander_finished(self):
        self._state_machine.force(PetState.IDLE)
        self._behavior_registry.trigger("idle", facing_left=self._facing_left)

    # ------------------------------------------------------------------
    # Sleep
    # ------------------------------------------------------------------

    def _check_sleep_conditions(self):
        if self._state_machine.is_busy:
            return

        if self._sleep_settings.get("schedule_enabled", False):
            if self._is_scheduled_sleep_time():
                self._enter_sleep()
                return

        timeout_ms = self._sleep_settings.get("inactivity_timeout_ms", 60000)
        elapsed_ms = (datetime.now() - self._last_activity_time).total_seconds() * 1000
        if elapsed_ms >= timeout_ms:
            self._enter_sleep()

    def _is_scheduled_sleep_time(self) -> bool:
        start_str = self._sleep_settings.get("schedule_start", "22:00")
        end_str = self._sleep_settings.get("schedule_end", "06:00")
        now = datetime.now().strftime("%H:%M")

        if start_str <= end_str:
            return start_str <= now < end_str
        else:
            return now >= start_str or now < end_str

    def _enter_sleep(self):
        if self._state_machine.transition(PetState.SLEEPING):
            logger.info("Pet is going to sleep")
            self._behavior_registry.trigger("sleep")

    def _wake_up(self):
        if self._state_machine.state != PetState.SLEEPING:
            return
        logger.info("Pet is waking up")
        self._state_machine.force(PetState.IDLE)
        self._last_activity_time = datetime.now()
        self._behavior_registry.trigger("wave")

    # ------------------------------------------------------------------
    # Speech bubble
    # ------------------------------------------------------------------

    def show_bubble(self, text: str, duration_ms: int | None = None) -> None:
        if not self._speech_bubble_settings.get("enabled", True):
            return
        if duration_ms is None:
            duration_ms = self._speech_bubble_settings.get("duration_ms", 3000)
        self._speech_bubble.update_position(self.pos(), self.size())
        self._speech_bubble.show_message(text, duration_ms)

    def show_notification(self, text: str, duration_ms: int = 5000, on_click=None) -> None:
        """Show a notification bubble. Optionally call on_click when pet is clicked."""
        self.show_bubble(text, duration_ms)
        self._notification_callback = on_click

    # ------------------------------------------------------------------
    # Time period transitions
    # ------------------------------------------------------------------

    def _get_current_period(self) -> str | None:
        periods = self._time_period_settings.get("periods", {})
        if not periods:
            return None

        now = datetime.now().strftime("%H:%M")
        sorted_periods = sorted(periods.items(), key=lambda item: item[1])

        current = sorted_periods[-1][0]
        for name, start_time in sorted_periods:
            if start_time <= now:
                current = name

        return current

    def _check_time_period_transition(self) -> None:
        current_period = self._get_current_period()
        previous = self._last_time_period
        self._last_time_period = current_period

        if previous is None:
            return

        if current_period == previous:
            return

        if self._state_machine.is_busy:
            logger.debug(
                f"Time period changed to {current_period} but pet is busy, skipping trigger"
            )
            return

        logger.info(f"Time period transition: {previous} -> {current_period}")

        greeting = self._time_period_settings.get("greetings", {}).get(current_period)
        if greeting:
            self.show_bubble(self._personalize_greeting(greeting))

    # ------------------------------------------------------------------
    # Qt event overrides
    # ------------------------------------------------------------------

    def moveEvent(self, event):
        super().moveEvent(event)
        self._speech_bubble.update_position(self.pos(), self.size())

    def paintEvent(self, event):
        if self._current_sprite.isNull():
            return

        painter = QPainter(self)
        x = (self.width() - self._current_sprite.width()) // 2
        y = (self.height() - self._current_sprite.height()) // 2
        painter.drawPixmap(x, y, self._current_sprite)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._system_move_pending = True
            self._last_activity_time = datetime.now()
            event.accept()

            if self._state_machine.state == PetState.SLEEPING:
                self._wake_up()
                return

            if self._state_machine.state == PetState.ALERTING:
                self.stop_alert()
                return

            # Handle notification callback
            if self._notification_callback:
                cb = self._notification_callback
                self._notification_callback = None
                cb()
                return

            self._tap_origin = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
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
        if event.button() == Qt.MouseButton.LeftButton:
            self._system_move_pending = False
            if self._tap_origin is not None:
                delta = event.globalPosition().toPoint() - self._tap_origin
                if abs(delta.x()) < 5 and abs(delta.y()) < 5:
                    self.clicked.emit()
                self._tap_origin = None
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        self._last_activity_time = datetime.now()
        if self._state_machine.state == PetState.SLEEPING:
            self._wake_up()

        menu = QMenu(self)

        reset_action = QAction("Reset Position", self)
        reset_action.triggered.connect(self._move_to_default_position)
        menu.addAction(reset_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        menu.exec(event.globalPos())

    # ------------------------------------------------------------------
    # Alert
    # ------------------------------------------------------------------

    def _quit_app(self):
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()

    @pyqtSlot(str)
    def trigger_alert(self, sender_name: str):
        """Trigger alert animation and sound."""
        if self._state_machine.state == PetState.ALERTING:
            return

        if self._state_machine.state == PetState.WANDERING:
            self._move_animation.stop()

        self._state_machine.force(PetState.ALERTING)
        self._behavior_registry.trigger("alert", {"sender": sender_name})

    def stop_alert(self):
        self._bounce_animation.stop()
        self._state_machine.force(PetState.IDLE)
        self._behavior_registry.stop_current()
