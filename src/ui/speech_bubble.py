"""Speech bubble widget that displays text near the pet."""

import logging
from collections import deque

from PyQt6.QtCore import QPoint, QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import QApplication, QWidget

logger = logging.getLogger(__name__)

BUBBLE_PADDING = 12
BUBBLE_RADIUS = 10
TAIL_WIDTH = 10
TAIL_HEIGHT = 8
BG_COLOR = QColor(255, 255, 255, 230)
BORDER_COLOR = QColor(80, 80, 80, 200)

BUBBLE_MARGIN = 8
TEXT_COLOR = QColor(40, 40, 40)
FONT_SIZE = 11


class SpeechBubble(QWidget):
    """A floating speech bubble that appears next to the pet."""

    def __init__(self):
        super().__init__()
        self._text = ""
        self._tail_on_left = True
        self._pet_pos = QPoint()
        self._pet_size = QSize()

        self._queue: deque[tuple[str, int]] = deque()

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.hide_bubble)

        self._setup_window()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def show_message(self, text: str, duration_ms: int = 3000) -> None:
        if self.isVisible():
            self._queue.append((text, duration_ms))
            return
        self._show_now(text, duration_ms)

    def _show_now(self, text: str, duration_ms: int) -> None:
        self._text = text
        self._resize_to_text()
        self._reposition()
        self.show()
        self.raise_()

        self._dismiss_timer.stop()
        if duration_ms > 0:
            self._dismiss_timer.start(duration_ms)

    def hide_bubble(self) -> None:
        self._dismiss_timer.stop()
        self.hide()
        if self._queue:
            text, dur = self._queue.popleft()
            self._show_now(text, dur)

    def update_position(self, pet_pos: QPoint, pet_size: QSize) -> None:
        self._pet_pos = pet_pos
        self._pet_size = pet_size
        if self.isVisible():
            self._reposition()

    def _resize_to_text(self):
        font = QFont()
        font.setPointSize(FONT_SIZE)
        metrics = QFontMetrics(font)

        max_width = 250
        bounding = metrics.boundingRect(
            0,
            0,
            max_width,
            0,
            Qt.TextFlag.TextWordWrap,
            self._text,
        )

        width = bounding.width() + BUBBLE_PADDING * 2 + TAIL_WIDTH
        height = bounding.height() + BUBBLE_PADDING * 2
        self.setFixedSize(max(width, 60), max(height, 30))

    def _reposition(self):
        if self._pet_size.isEmpty():
            return

        screen = self.screen() or QApplication.primaryScreen()
        if not screen:
            return
        screen_geo = screen.availableGeometry()

        bubble_w = self.width()
        bubble_h = self.height()

        right_x = self._pet_pos.x() + self._pet_size.width() + BUBBLE_MARGIN
        if right_x + bubble_w <= screen_geo.right():
            x = right_x
            self._tail_on_left = True
        else:
            x = self._pet_pos.x() - bubble_w - BUBBLE_MARGIN
            self._tail_on_left = False

        # Center bubble vertically on pet
        pet_center_y = self._pet_pos.y() + self._pet_size.height() // 2
        y = pet_center_y - bubble_h // 2
        y = max(screen_geo.top(), min(y, screen_geo.bottom() - bubble_h))

        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        if self._tail_on_left:
            bubble_rect = QRectF(TAIL_WIDTH, 0, w - TAIL_WIDTH, h)
        else:
            bubble_rect = QRectF(0, 0, w - TAIL_WIDTH, h)

        # Bubble body
        path = QPainterPath()
        path.addRoundedRect(bubble_rect, BUBBLE_RADIUS, BUBBLE_RADIUS)

        # Tail
        tail_path = QPainterPath()
        center_y = h / 2
        if self._tail_on_left:
            tail_path.moveTo(TAIL_WIDTH, center_y - TAIL_HEIGHT / 2)
            tail_path.lineTo(0, center_y)
            tail_path.lineTo(TAIL_WIDTH, center_y + TAIL_HEIGHT / 2)
        else:
            tail_path.moveTo(w - TAIL_WIDTH, center_y - TAIL_HEIGHT / 2)
            tail_path.lineTo(w, center_y)
            tail_path.lineTo(w - TAIL_WIDTH, center_y + TAIL_HEIGHT / 2)
        tail_path.closeSubpath()

        full_path = path.united(tail_path)

        painter.setPen(QPen(BORDER_COLOR, 1.5))
        painter.setBrush(BG_COLOR)
        painter.drawPath(full_path)

        # Text
        font = QFont()
        font.setPointSize(FONT_SIZE)
        painter.setFont(font)
        painter.setPen(TEXT_COLOR)
        painter.drawText(
            bubble_rect.adjusted(BUBBLE_PADDING, 0, -BUBBLE_PADDING, 0),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self._text,
        )

        painter.end()
