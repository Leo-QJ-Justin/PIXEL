"""MapleStory-style dialog box and button widgets using 9-slice sprite rendering."""

import logging
from pathlib import Path

from PyQt6.QtCore import QPoint, QRect, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"

# 9-slice insets (measured from the asset images)
# Dialog frame (679x273): blue gradient border ~25px
DIALOG_SLICE_LEFT = 28
DIALOG_SLICE_TOP = 28
DIALOG_SLICE_RIGHT = 28
DIALOG_SLICE_BOTTOM = 28

# Button (~98x44 / ~94x48): rounded 3D edge ~14px
BUTTON_SLICE_LEFT = 14
BUTTON_SLICE_TOP = 14
BUTTON_SLICE_RIGHT = 14
BUTTON_SLICE_BOTTOM = 14

# Dialog layout constants
DIALOG_WIDTH = 420
DIALOG_MIN_HEIGHT = 200
DIALOG_CONTENT_PADDING = 16
PORTRAIT_SIZE = 64

# Text colors
TITLE_COLOR = QColor(30, 60, 100)
BODY_COLOR = QColor(40, 40, 40)
BUTTON_TEXT_COLOR = QColor(255, 255, 255)
BUTTON_SHADOW_COLOR = QColor(0, 0, 0, 80)

# Form styling (scoped to form container only)
_FORM_WIDGET_STYLE = """
QLineEdit {
    background-color: #ffffff;
    color: #282828;
    border: 1px solid #a0c0e0;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 10pt;
    selection-background-color: #4a9eda;
}
QLineEdit:focus {
    border: 2px solid #4a9eda;
}
QComboBox {
    background-color: #ffffff;
    color: #282828;
    border: 1px solid #a0c0e0;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 10pt;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #282828;
    border: 1px solid #a0c0e0;
    selection-background-color: #d0e8f8;
}
QLabel {
    color: #282828;
    font-size: 10pt;
    background: transparent;
}
"""


def draw_nine_slice(
    painter: QPainter,
    pixmap: QPixmap,
    target: QRect,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> None:
    """Draw a pixmap stretched using 9-slice scaling.

    The pixmap is divided into 9 regions: 4 corners (fixed size),
    4 edges (stretch in one axis), and 1 center (stretches in both).
    """
    if pixmap.isNull():
        return

    pw = pixmap.width()
    ph = pixmap.height()
    tx, ty, tw, th = target.x(), target.y(), target.width(), target.height()

    # Clamp insets to avoid negative center regions
    left = min(left, tw // 2, pw // 2)
    top = min(top, th // 2, ph // 2)
    right = min(right, tw // 2, pw // 2)
    bottom = min(bottom, th // 2, ph // 2)

    # Source regions (from the pixmap)
    src_center_w = pw - left - right
    src_center_h = ph - top - bottom

    # Target regions
    tgt_center_w = tw - left - right
    tgt_center_h = th - top - bottom

    # Disable smooth scaling for crisp pixel edges
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

    slices = [
        # (target_rect, source_rect)
        # Top-left corner
        (QRect(tx, ty, left, top), QRect(0, 0, left, top)),
        # Top edge
        (QRect(tx + left, ty, tgt_center_w, top), QRect(left, 0, src_center_w, top)),
        # Top-right corner
        (QRect(tx + tw - right, ty, right, top), QRect(pw - right, 0, right, top)),
        # Left edge
        (QRect(tx, ty + top, left, tgt_center_h), QRect(0, top, left, src_center_h)),
        # Center
        (
            QRect(tx + left, ty + top, tgt_center_w, tgt_center_h),
            QRect(left, top, src_center_w, src_center_h),
        ),
        # Right edge
        (
            QRect(tx + tw - right, ty + top, right, tgt_center_h),
            QRect(pw - right, top, right, src_center_h),
        ),
        # Bottom-left corner
        (QRect(tx, ty + th - bottom, left, bottom), QRect(0, ph - bottom, left, bottom)),
        # Bottom edge
        (
            QRect(tx + left, ty + th - bottom, tgt_center_w, bottom),
            QRect(left, ph - bottom, src_center_w, bottom),
        ),
        # Bottom-right corner
        (
            QRect(tx + tw - right, ty + th - bottom, right, bottom),
            QRect(pw - right, ph - bottom, right, bottom),
        ),
    ]

    for tgt_rect, src_rect in slices:
        if tgt_rect.width() > 0 and tgt_rect.height() > 0:
            painter.drawPixmap(tgt_rect, pixmap, src_rect)


def _load_asset(name: str) -> QPixmap:
    """Load a PNG asset from the assets directory."""
    path = ASSETS_DIR / name
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        logger.warning(f"Could not load asset: {path}")
    return pixmap


class MapleButton(QPushButton):
    """A MapleStory-styled push button using 9-slice sprite rendering."""

    def __init__(self, text: str, sprite: QPixmap, parent: QWidget | None = None):
        super().__init__(text, parent)
        self._sprite = sprite
        self._hovered = False
        self._pressed = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self.setMinimumWidth(90)

        # Size to fit text
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        self.setFixedWidth(max(90, text_width + 36))

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        target = QRect(0, 0, self.width(), self.height())

        # Draw button sprite via 9-slice
        if not self._sprite.isNull():
            draw_nine_slice(
                painter,
                self._sprite,
                target,
                BUTTON_SLICE_LEFT,
                BUTTON_SLICE_TOP,
                BUTTON_SLICE_RIGHT,
                BUTTON_SLICE_BOTTOM,
            )

        # Apply hover/press overlay
        if self._pressed:
            painter.fillRect(target, QColor(0, 0, 0, 40))
        elif self._hovered:
            painter.fillRect(target, QColor(255, 255, 255, 40))

        # Draw text with shadow
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        text_rect = QRectF(target)
        if self._pressed:
            text_rect.translate(0, 1)

        # Shadow
        shadow_rect = text_rect.translated(1, 1)
        painter.setPen(BUTTON_SHADOW_COLOR)
        painter.drawText(shadow_rect, Qt.AlignmentFlag.AlignCenter, self.text())

        # Text
        painter.setPen(BUTTON_TEXT_COLOR)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())

        painter.end()


class DialogBox(QDialog):
    """A MapleStory-styled dialog box with 9-slice frame rendering."""

    def __init__(
        self,
        title: str,
        body_text: str = "",
        portrait_pixmap: QPixmap | None = None,
        buttons: list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._title = title
        self._portrait = portrait_pixmap
        self._drag_position: QPoint | None = None

        # Load frame sprite
        self._frame_sprite = _load_asset("dialog_frame.png")

        # Load button sprites
        self._button_sprites = {
            "accept": _load_asset("button_yellow.png"),
            "reject": _load_asset("button_pink.png"),
        }

        self._setup_window()
        self._build_layout(body_text, buttons or [("OK", "accept")])

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(DIALOG_WIDTH)
        self.setMinimumHeight(DIALOG_MIN_HEIGHT)

    def _build_layout(self, body_text: str, buttons: list[tuple[str, str]]):
        # Calculate content margins based on frame border + padding
        frame_border = max(DIALOG_SLICE_LEFT, DIALOG_SLICE_TOP, DIALOG_SLICE_RIGHT)
        margin = frame_border + DIALOG_CONTENT_PADDING

        # Extra right margin for portrait
        right_margin = margin
        if self._portrait and not self._portrait.isNull():
            right_margin = margin + PORTRAIT_SIZE + DIALOG_CONTENT_PADDING

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(margin, margin, right_margin, frame_border + 8)
        main_layout.setSpacing(12)

        # Title label
        title_label = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {TITLE_COLOR.name()}; background: transparent;")
        title_label.setWordWrap(True)
        main_layout.addWidget(title_label)

        # Body text label
        self._body_label = QLabel(body_text)
        self._body_label.setWordWrap(True)
        self._body_label.setStyleSheet(
            f"color: {BODY_COLOR.name()}; font-size: 10pt; background: transparent;"
        )
        if body_text:
            main_layout.addWidget(self._body_label)

        # Form area (initially hidden, populated via add_form_row)
        self._form_widget = QWidget()
        self._form_widget.setStyleSheet(_FORM_WIDGET_STYLE)
        self._form_layout = QVBoxLayout(self._form_widget)
        self._form_layout.setContentsMargins(0, 0, 0, 0)
        self._form_layout.setSpacing(8)
        self._form_widget.hide()
        main_layout.addWidget(self._form_widget)

        # Stretch to push buttons to the bottom
        main_layout.addStretch()

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        for label, role in buttons:
            sprite = self._button_sprites.get(role, self._button_sprites["accept"])
            btn = MapleButton(label, sprite, self)
            if role == "accept":
                btn.clicked.connect(self.accept)
            else:
                btn.clicked.connect(self.reject)
            button_layout.addWidget(btn)
            button_layout.addSpacing(8)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def set_body_html(self, html: str) -> None:
        """Set body text using HTML for styled content."""
        self._body_label.setText(html)
        self._body_label.setTextFormat(Qt.TextFormat.RichText)
        if not self._body_label.isVisible():
            # Re-insert body label into layout if it was hidden
            layout = self.layout()
            if layout:
                layout.insertWidget(1, self._body_label)
            self._body_label.show()

    def add_form_row(self, label: str, widget: QWidget) -> None:
        """Add a labeled form row to the dialog."""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)
        lbl = QLabel(label)
        lbl.setFixedWidth(70)
        row_layout.addWidget(lbl)
        row_layout.addWidget(widget, 1)
        self._form_layout.addLayout(row_layout)
        self._form_widget.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw dialog frame via 9-slice
        if not self._frame_sprite.isNull():
            draw_nine_slice(
                painter,
                self._frame_sprite,
                QRect(0, 0, self.width(), self.height()),
                DIALOG_SLICE_LEFT,
                DIALOG_SLICE_TOP,
                DIALOG_SLICE_RIGHT,
                DIALOG_SLICE_BOTTOM,
            )

        # Draw portrait in top-right area
        if self._portrait and not self._portrait.isNull():
            frame_border = max(DIALOG_SLICE_RIGHT, DIALOG_SLICE_TOP)
            portrait_x = self.width() - PORTRAIT_SIZE - frame_border - DIALOG_CONTENT_PADDING
            portrait_y = frame_border + DIALOG_CONTENT_PADDING

            scaled = self._portrait.scaled(
                PORTRAIT_SIZE,
                PORTRAIT_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Center the scaled pixmap in the portrait area
            px = portrait_x + (PORTRAIT_SIZE - scaled.width()) // 2
            py = portrait_y + (PORTRAIT_SIZE - scaled.height()) // 2
            painter.drawPixmap(px, py, scaled)

        painter.end()

    def showEvent(self, event):
        """Center dialog on screen when shown."""
        super().showEvent(event)
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

    def mousePressEvent(self, event):
        """Start drag if clicking on the title bar area."""
        if event.button() == Qt.MouseButton.LeftButton:
            frame_border = DIALOG_SLICE_TOP
            if event.position().y() <= frame_border + 50:
                self._drag_position = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Drag the dialog."""
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """End drag."""
        self._drag_position = None
        super().mouseReleaseEvent(event)
