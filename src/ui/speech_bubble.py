"""Speech bubble widget that displays text near the pet."""

import logging
from collections import deque
from pathlib import Path

from PyQt6.QtCore import QPoint, QRect, QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTransform,
)
from PyQt6.QtWidgets import QApplication, QWidget

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"

# 9-slice insets for the speech bubble sprite (118x120)
# The bubble has ~12px border on top/left/right and ~24px at bottom (tail area)
SPRITE_SLICE_LEFT = 16
SPRITE_SLICE_TOP = 16
SPRITE_SLICE_RIGHT = 16
SPRITE_SLICE_BOTTOM = 30  # Larger to accommodate tail

# Padding for text inside the bubble (relative to the 9-slice content area)
SPRITE_TEXT_PADDING = 8

# Fallback appearance constants (used when sprite asset is missing)
BUBBLE_PADDING = 12
BUBBLE_RADIUS = 10
TAIL_WIDTH = 10
TAIL_HEIGHT = 8
BG_COLOR = QColor(255, 255, 255, 230)
BORDER_COLOR = QColor(80, 80, 80, 200)

BUBBLE_MARGIN = 8  # Gap between pet and bubble
TEXT_COLOR = QColor(40, 40, 40)
FONT_SIZE = 11


class SpeechBubble(QWidget):
    """A floating speech bubble that appears next to the pet."""

    def __init__(self):
        super().__init__()
        self._text = ""
        self._tail_on_left = True  # Tail points left (bubble is to the right of pet)
        self._pet_pos = QPoint()
        self._pet_size = QSize()

        self._queue: deque[tuple[str, int]] = deque()

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.hide_bubble)

        # Load sprite asset
        self._sprite = self._load_sprite()
        self._sprite_flipped = QPixmap()
        if not self._sprite.isNull():
            flip = QTransform().scale(-1, 1)
            self._sprite_flipped = self._sprite.transformed(flip)

        self._setup_window()

    @staticmethod
    def _load_sprite() -> QPixmap:
        """Load the speech bubble sprite asset."""
        path = ASSETS_DIR / "speech_bubble.png"
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            logger.info("Speech bubble sprite not found, using fallback rendering")
        else:
            logger.debug(f"Loaded speech bubble sprite: {path}")
        return pixmap

    @property
    def _use_sprite(self) -> bool:
        return not self._sprite.isNull()

    def _setup_window(self):
        """Configure window properties for a floating bubble."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def show_message(self, text: str, duration_ms: int = 3000) -> None:
        """Show a speech bubble, queuing if one is already visible."""
        if self.isVisible():
            self._queue.append((text, duration_ms))
            logger.debug(f"Speech bubble queued: {text}")
            return
        self._show_now(text, duration_ms)

    def _show_now(self, text: str, duration_ms: int) -> None:
        """Display a message immediately (no queue check)."""
        self._text = text
        self._resize_to_text()
        self._reposition()
        self.show()
        self.raise_()

        self._dismiss_timer.stop()
        if duration_ms > 0:
            self._dismiss_timer.start(duration_ms)

        logger.debug(f"Speech bubble shown: {text}")

    def hide_bubble(self) -> None:
        """Hide the bubble and show next queued message if any."""
        self._dismiss_timer.stop()
        self.hide()
        if self._queue:
            text, dur = self._queue.popleft()
            self._show_now(text, dur)

    def update_position(self, pet_pos: QPoint, pet_size: QSize) -> None:
        """Reposition bubble relative to the pet."""
        self._pet_pos = pet_pos
        self._pet_size = pet_size
        if self.isVisible():
            self._reposition()

    def _resize_to_text(self):
        """Resize widget to fit the current text."""
        font = QFont()
        font.setPointSize(FONT_SIZE)
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(self._text)

        if self._use_sprite:
            # Account for 9-slice border insets
            h_inset = SPRITE_SLICE_LEFT + SPRITE_SLICE_RIGHT
            v_inset = SPRITE_SLICE_TOP + SPRITE_SLICE_BOTTOM
            width = text_rect.width() + h_inset + SPRITE_TEXT_PADDING * 2
            height = text_rect.height() + v_inset + SPRITE_TEXT_PADDING * 2
            self.setFixedSize(max(width, 80), max(height, 50))
        else:
            width = text_rect.width() + BUBBLE_PADDING * 2 + TAIL_WIDTH
            height = text_rect.height() + BUBBLE_PADDING * 2
            self.setFixedSize(max(width, 60), max(height, 30))

    def _reposition(self):
        """Position the bubble next to the pet, flipping sides if needed."""
        if self._pet_size.isEmpty():
            return

        screen = QApplication.primaryScreen()
        if not screen:
            return
        screen_geo = screen.availableGeometry()

        bubble_w = self.width()
        bubble_h = self.height()

        # Try right side first
        right_x = self._pet_pos.x() + self._pet_size.width() + BUBBLE_MARGIN
        if right_x + bubble_w <= screen_geo.right():
            x = right_x
            self._tail_on_left = True
        else:
            # Flip to left side
            x = self._pet_pos.x() - bubble_w - BUBBLE_MARGIN
            self._tail_on_left = False

        # Align with top of pet sprite
        y = self._pet_pos.y() - bubble_h + BUBBLE_MARGIN
        # Clamp to screen
        y = max(screen_geo.top(), min(y, screen_geo.bottom() - bubble_h))

        self.move(x, y)

    def paintEvent(self, event):
        """Draw the speech bubble."""
        if self._use_sprite:
            self._paint_sprite(event)
        else:
            self._paint_fallback(event)

    def _paint_sprite(self, event):
        """Draw the speech bubble using 9-slice sprite rendering."""
        from src.ui.dialog_box import draw_nine_slice

        painter = QPainter(self)

        w = self.width()
        h = self.height()

        # Choose sprite and insets based on tail direction
        if self._tail_on_left:
            sprite = self._sprite
            left, top, right, bottom = (
                SPRITE_SLICE_LEFT,
                SPRITE_SLICE_TOP,
                SPRITE_SLICE_RIGHT,
                SPRITE_SLICE_BOTTOM,
            )
        else:
            sprite = self._sprite_flipped
            # Swap left/right insets for flipped sprite
            left, top, right, bottom = (
                SPRITE_SLICE_RIGHT,
                SPRITE_SLICE_TOP,
                SPRITE_SLICE_LEFT,
                SPRITE_SLICE_BOTTOM,
            )

        draw_nine_slice(painter, sprite, QRect(0, 0, w, h), left, top, right, bottom)

        # Draw text in the content area (inside the border insets)
        font = QFont()
        font.setPointSize(FONT_SIZE)
        painter.setFont(font)
        painter.setPen(TEXT_COLOR)

        content_rect = QRectF(
            left + SPRITE_TEXT_PADDING,
            top + SPRITE_TEXT_PADDING,
            w - left - right - SPRITE_TEXT_PADDING * 2,
            h - top - bottom - SPRITE_TEXT_PADDING * 2,
        )
        painter.drawText(content_rect, Qt.AlignmentFlag.AlignCenter, self._text)

        painter.end()

    def _paint_fallback(self, event):
        """Draw the speech bubble with programmatic rounded rect and tail."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Determine bubble rect (leave room for tail)
        if self._tail_on_left:
            bubble_rect = QRectF(TAIL_WIDTH, 0, w - TAIL_WIDTH, h)
        else:
            bubble_rect = QRectF(0, 0, w - TAIL_WIDTH, h)

        # Draw bubble body
        path = QPainterPath()
        path.addRoundedRect(bubble_rect, BUBBLE_RADIUS, BUBBLE_RADIUS)

        # Draw tail
        tail_path = QPainterPath()
        center_y = h / 2
        tail_height = 8
        if self._tail_on_left:
            tail_path.moveTo(TAIL_WIDTH, center_y - tail_height / 2)
            tail_path.lineTo(0, center_y)
            tail_path.lineTo(TAIL_WIDTH, center_y + tail_height / 2)
        else:
            tail_path.moveTo(w - TAIL_WIDTH, center_y - tail_height / 2)
            tail_path.lineTo(w, center_y)
            tail_path.lineTo(w - TAIL_WIDTH, center_y + tail_height / 2)
        tail_path.closeSubpath()

        full_path = path.united(tail_path)

        painter.setPen(QPen(BORDER_COLOR, 1.5))
        painter.setBrush(BG_COLOR)
        painter.drawPath(full_path)

        # Draw text
        font = QFont()
        font.setPointSize(FONT_SIZE)
        painter.setFont(font)
        painter.setPen(TEXT_COLOR)
        painter.drawText(
            bubble_rect.adjusted(BUBBLE_PADDING, 0, -BUBBLE_PADDING, 0),
            Qt.AlignmentFlag.AlignCenter,
            self._text,
        )

        painter.end()
