import logging
import random
from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtSlot, QTimer
from PyQt6.QtGui import QPainter, QPixmap, QAction, QTransform
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
from config import SPRITES_DIR, SOUNDS_DIR

logger = logging.getLogger(__name__)


class HaroWidget(QWidget):
    """Main Haro desktop pet widget."""

    def __init__(self):
        super().__init__()
        self._drag_position = QPoint()
        self._is_alerting = False
        self._animation = None

        # Load idle sprites (idle_1.png, idle_2.png or fallback to idle.png)
        self._idle_sprites = []
        for i in range(1, 3):
            path = SPRITES_DIR / f"idle_{i}.png"
            if path.exists():
                self._idle_sprites.append(QPixmap(str(path)))
        if not self._idle_sprites:
            fallback = SPRITES_DIR / "idle.png"
            if fallback.exists():
                self._idle_sprites.append(QPixmap(str(fallback)))

        # Load alert sprites (alert_1.png, alert_2.png or fallback to alert.png)
        self._alert_sprites = []
        for i in range(1, 3):
            path = SPRITES_DIR / f"alert_{i}.png"
            if path.exists():
                self._alert_sprites.append(QPixmap(str(path)))
        if not self._alert_sprites:
            fallback = SPRITES_DIR / "alert.png"
            if fallback.exists():
                self._alert_sprites.append(QPixmap(str(fallback)))

        self._idle_frame = 0
        self._alert_frame = 0
        self._current_sprite = self._idle_sprites[0] if self._idle_sprites else QPixmap()

        # Load sound
        self._alert_sound = QSoundEffect()
        sound_path = SOUNDS_DIR / "haro_alert.wav"
        if sound_path.exists():
            self._alert_sound.setSource(QUrl.fromLocalFile(str(sound_path)))

        # Load fly sprites for wandering animation
        self._fly_sprites = []
        for i in range(1, 5):
            path = SPRITES_DIR / f"fly_{i}.png"
            if path.exists():
                self._fly_sprites.append(QPixmap(str(path)))
        self._can_fly = len(self._fly_sprites) == 4

        self._is_wandering = False
        self._current_frame = 0
        self._facing_left = False

        # Create flipped versions for left-facing movement
        flip_transform = QTransform().scale(-1, 1)

        self._idle_sprites_flipped = []
        for sprite in self._idle_sprites:
            self._idle_sprites_flipped.append(sprite.transformed(flip_transform))

        self._fly_sprites_flipped = []
        for sprite in self._fly_sprites:
            self._fly_sprites_flipped.append(sprite.transformed(flip_transform))

        self._setup_window()
        self._setup_animation()
        self._setup_wandering()

    def _setup_window(self):
        """Configure window properties for a desktop pet."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set size based on largest sprite
        max_width = 100
        max_height = 100
        for sprite in self._idle_sprites + self._alert_sprites + self._fly_sprites:
            if not sprite.isNull():
                max_width = max(max_width, sprite.width())
                max_height = max(max_height, sprite.height())
        self.setFixedSize(max_width, max_height)

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

    def _setup_animation(self):
        """Setup bounce animation for alerts."""
        self._animation = QPropertyAnimation(self, b"pos")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        self._animation.setLoopCount(10)

        # Idle animation timer (cycle idle frames)
        self._idle_timer = QTimer()
        self._idle_timer.timeout.connect(self._next_idle_frame)
        if len(self._idle_sprites) > 1:
            self._idle_timer.start(500)

        # Alert animation timer (cycle alert frames)
        self._alert_timer = QTimer()
        self._alert_timer.timeout.connect(self._next_alert_frame)

    def _next_idle_frame(self):
        """Cycle to next idle animation frame."""
        if self._is_alerting or self._is_wandering or not self._idle_sprites:
            return
        self._idle_frame = (self._idle_frame + 1) % len(self._idle_sprites)
        sprites = self._idle_sprites_flipped if self._facing_left else self._idle_sprites
        self._current_sprite = sprites[self._idle_frame]
        self.update()

    def _next_alert_frame(self):
        """Cycle to next alert animation frame."""
        if not self._alert_sprites:
            return
        self._alert_frame = (self._alert_frame + 1) % len(self._alert_sprites)
        self._current_sprite = self._alert_sprites[self._alert_frame]
        self.update()

    def _setup_wandering(self):
        """Setup timers and animations for wandering behavior."""
        # Wander decision timer (triggers every 5-15s)
        self._wander_timer = QTimer()
        self._wander_timer.timeout.connect(self._maybe_wander)
        self._wander_timer.start(random.randint(5000, 15000))

        # Animation frame timer (100ms per frame during flight)
        self._frame_timer = QTimer()
        self._frame_timer.timeout.connect(self._next_frame)

        # Movement animation
        self._move_anim = QPropertyAnimation(self, b"pos")
        self._move_anim.setDuration(1500)
        self._move_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._move_anim.finished.connect(self._stop_wander)

    def _maybe_wander(self):
        """Randomly decide to wander."""
        # Reset timer with random interval
        self._wander_timer.setInterval(random.randint(5000, 15000))

        # Don't wander if alerting or already wandering
        if self._is_alerting or self._is_wandering:
            return

        # 30% chance to wander
        if random.random() < 0.3:
            self._start_wander()

    def _start_wander(self):
        """Start wandering to a random position."""
        self._is_wandering = True

        # Get screen bounds
        screen = self.screen()
        if not screen:
            return
        geo = screen.availableGeometry()

        # Pick random destination nearby (x-axis only, stay above taskbar)
        current_x = self.pos().x()
        move_distance = random.randint(50, 150) * random.choice([-1, 1])
        dest_x = current_x + move_distance

        # Clamp to screen bounds with margin
        min_x = geo.left()
        max_x = geo.right() - self.width()
        dest_x = max(min_x, min(dest_x, max_x))

        dest_y = self.pos().y()  # Keep same y position

        # Set facing direction based on movement
        self._facing_left = dest_x < current_x

        # Start movement animation
        self._move_anim.setStartValue(self.pos())
        self._move_anim.setEndValue(QPoint(dest_x, dest_y))
        self._move_anim.start()

        # Start frame animation if fly sprites available
        if self._can_fly:
            self._current_frame = 0
            sprites = self._fly_sprites_flipped if self._facing_left else self._fly_sprites
            self._current_sprite = sprites[0]
            self._frame_timer.start(100)
            self.update()

    def _next_frame(self):
        """Cycle to next fly animation frame."""
        if not self._can_fly:
            return
        self._current_frame = (self._current_frame + 1) % 4
        sprites = self._fly_sprites_flipped if self._facing_left else self._fly_sprites
        self._current_sprite = sprites[self._current_frame]
        self.update()

    def _stop_wander(self):
        """Stop wandering and return to idle."""
        self._is_wandering = False
        self._frame_timer.stop()
        self._idle_frame = 0
        if self._idle_sprites:
            sprites = self._idle_sprites_flipped if self._facing_left else self._idle_sprites
            self._current_sprite = sprites[0]
        else:
            self._current_sprite = QPixmap()
        self.update()

    def paintEvent(self, event):
        """Draw the current sprite centered in the widget."""
        painter = QPainter(self)
        x = (self.width() - self._current_sprite.width()) // 2
        y = (self.height() - self._current_sprite.height()) // 2
        painter.drawPixmap(x, y, self._current_sprite)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging and alert dismissal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

            # Dismiss alert on click
            if self._is_alerting:
                self.stop_alert()

    def mouseMoveEvent(self, event):
        """Handle dragging the widget."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
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
        """Trigger alert animation and sound."""
        logger.debug(f"trigger_alert called for: {sender_name}")
        if self._is_alerting:
            logger.debug("Already alerting, skipping")
            return
        logger.info(f"Starting alert for: {sender_name}")

        # Stop any ongoing wander
        if self._is_wandering:
            self._stop_wander()
            self._move_anim.stop()

        self._is_alerting = True

        # Change sprite and start alert animation
        if self._alert_sprites:
            self._alert_frame = 0
            self._current_sprite = self._alert_sprites[0]
            if len(self._alert_sprites) > 1:
                self._alert_timer.start(300)
            self.update()

        # Play sound
        if self._alert_sound.isLoaded():
            self._alert_sound.play()

        # Start bounce animation
        if self._animation:
            start_pos = self.pos()
            bounce_pos = QPoint(start_pos.x(), start_pos.y() - 20)
            self._animation.setStartValue(bounce_pos)
            self._animation.setEndValue(start_pos)
            self._animation.start()

    def stop_alert(self):
        """Stop the alert and return to idle state."""
        self._is_alerting = False

        # Stop alert animation timer
        self._alert_timer.stop()

        # Reset sprite to idle
        self._idle_frame = 0
        self._current_sprite = self._idle_sprites[0] if self._idle_sprites else QPixmap()
        self.update()

        # Stop bounce animation
        if self._animation:
            self._animation.stop()
