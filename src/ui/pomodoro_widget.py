"""Warm dark claymorphism Pomodoro timer floating widget."""

import logging
from datetime import date, timedelta

from PyQt6.QtCore import QPoint, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import load_settings, save_settings
from src.ui import pomodoro_theme as theme

logger = logging.getLogger(__name__)


class ProgressRing(QWidget):
    """Circular progress ring drawn with QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(theme.RING_SIZE, theme.RING_SIZE)
        self._progress = 1.0  # 0.0 to 1.0
        self._color = QColor(theme.COLORS["ring_focus"])

    def set_progress(self, progress: float) -> None:
        self._progress = max(0.0, min(1.0, progress))
        self.update()

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(
            theme.RING_THICKNESS / 2,
            theme.RING_THICKNESS / 2,
            self.width() - theme.RING_THICKNESS,
            self.height() - theme.RING_THICKNESS,
        )

        # Background track
        painter.setPen(
            QPen(QColor(theme.COLORS["diamond_empty"]), theme.RING_THICKNESS, Qt.PenStyle.SolidLine)
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)

        # Progress arc (Qt uses 1/16th degree units, starts at 12 o'clock = 90°)
        if self._progress > 0:
            span = int(self._progress * 360 * 16)
            painter.setPen(QPen(self._color, theme.RING_THICKNESS, Qt.PenStyle.SolidLine))
            painter.drawArc(rect, 90 * 16, -span)

        painter.end()


class DiamondStreak(QWidget):
    """Row of diamond shapes showing cycle progress."""

    def __init__(self, count: int = 4, parent=None):
        super().__init__(parent)
        self._count = count
        self._filled = 0
        self.setFixedHeight(20)
        self.setMinimumWidth(count * 20)

    def set_filled(self, n: int) -> None:
        self._filled = n
        self.update()

    def set_count(self, n: int) -> None:
        self._count = n
        self.setMinimumWidth(n * 20)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = 10
        spacing = 20
        total_w = self._count * spacing
        start_x = (self.width() - total_w) / 2 + spacing / 2

        for i in range(self._count):
            cx = start_x + i * spacing
            cy = self.height() / 2

            painter.save()
            painter.translate(cx, cy)
            painter.rotate(45)

            color = (
                QColor(theme.COLORS["diamond_filled"])
                if i < self._filled
                else QColor(theme.COLORS["diamond_empty"])
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRect(QRectF(-size / 2, -size / 2, size, size))
            painter.restore()

        painter.end()


class WeeklyChart(QWidget):
    """Bar chart showing sessions per day for the last 7 days."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict[str, int] = {}
        self.setFixedHeight(100)

    def set_data(self, daily: dict[str, int]) -> None:
        self._data = daily
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        today = date.today()
        days = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            days.append((d.strftime("%a")[0], self._data.get(d.isoformat(), 0)))

        max_val = max((v for _, v in days), default=1) or 1
        w = self.width()
        h = self.height()
        bar_w = max(w // 9, 8)
        spacing = (w - bar_w * 7) / 8
        label_h = 16
        chart_h = h - label_h - 4

        for idx, (label, val) in enumerate(days):
            x = spacing + idx * (bar_w + spacing)
            bar_h = (val / max_val) * chart_h if val > 0 else 0
            y = h - label_h - bar_h

            # Bar
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QColor(theme.COLORS["chart_bar"])
                if val > 0
                else QColor(theme.COLORS["chart_empty"])
            )
            painter.drawRoundedRect(QRectF(x, y, bar_w, bar_h), 2, 2)

            # Label
            painter.setPen(QColor(theme.COLORS["text_muted"]))
            painter.setFont(QFont("sans-serif", 7))
            painter.drawText(
                QRectF(x, h - label_h, bar_w, label_h),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

        painter.end()


class PomodoroWidget(QWidget):
    """Floating MapleStory-themed Pomodoro timer window."""

    closed = pyqtSignal()

    def __init__(self, integration, parent=None):
        super().__init__(parent)
        self._integration = integration
        self._drag_position: QPoint | None = None
        self._total_seconds = 0
        self._font_family = self._load_font()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(theme.WIDGET_WIDTH)

        self._stack = QStackedWidget()
        self._build_timer_view()
        self._build_settings_view()
        self._build_stats_view()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addWidget(self._stack)

        # Connect integration signals
        integration.timer_tick.connect(self._on_tick)
        integration.state_changed.connect(self._on_state_changed)
        integration.session_completed.connect(self._on_session_completed)
        integration.stats_updated.connect(self._on_stats_updated)

        self._update_button_visibility("IDLE")
        self.adjustSize()

    # -- Header --

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("pomo_header")
        header.setFixedHeight(36)
        header.setStyleSheet(theme.header_style(self._font_family))
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 6, 0)

        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background: {theme.COLORS['accent']};" "border-radius: 6px;")
        layout.addWidget(dot)

        title = QLabel("Focus Timer")
        title.setStyleSheet(
            f"color: {theme.COLORS['accent']}; font-weight: bold; font-size: 11pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        layout.addWidget(title)
        layout.addStretch()

        close_btn = QPushButton("\u2715")
        close_btn.setStyleSheet(theme.close_button_style())
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)

        return header

    # -- Timer View --

    def _build_timer_view(self) -> None:
        page = QWidget()
        page.setStyleSheet(theme.timer_page_style())
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Progress ring + countdown overlay
        ring_container = QWidget()
        ring_container.setStyleSheet("background: transparent;")
        ring_layout = QVBoxLayout(ring_container)
        ring_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._ring = ProgressRing()
        ring_layout.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignCenter)

        # Overlay countdown on top of ring
        self._countdown_label = QLabel("00:00")
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._countdown_label.setStyleSheet(
            f"color: {theme.COLORS['text']}; font-size: 28pt; font-weight: bold;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        self._countdown_label.setParent(self._ring)
        self._countdown_label.setGeometry(0, 0, theme.RING_SIZE, theme.RING_SIZE)

        layout.addWidget(ring_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Phase label
        self._phase_label = QLabel("Ready to focus?")
        self._phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._phase_label.setStyleSheet(
            f"color: {theme.COLORS['text_muted']}; font-size: 10pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        layout.addWidget(self._phase_label)

        # Diamonds
        sessions_per_cycle = self._integration._settings.get("sessions_per_cycle", 4)
        self._diamonds = DiamondStreak(sessions_per_cycle)
        layout.addWidget(self._diamonds, alignment=Qt.AlignmentFlag.AlignCenter)

        # Button rows
        self._btn_container = QWidget()
        self._btn_container.setStyleSheet("background: transparent;")
        self._btn_layout = QVBoxLayout(self._btn_container)
        self._btn_layout.setContentsMargins(0, 4, 0, 0)
        self._btn_layout.setSpacing(4)

        # Row 1: primary buttons
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self._start_btn = QPushButton("START")
        self._start_btn.setStyleSheet(theme.start_button_style(self._font_family))
        self._start_btn.clicked.connect(self._integration.start_session)
        row1.addWidget(self._start_btn)

        self._pause_btn = QPushButton("PAUSE")
        self._pause_btn.setStyleSheet(theme.start_button_style(self._font_family))
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        row1.addWidget(self._pause_btn)

        self._skip_btn = QPushButton("SKIP")
        self._skip_btn.setStyleSheet(theme.skip_button_style(self._font_family))
        self._skip_btn.clicked.connect(self._integration.skip)
        row1.addWidget(self._skip_btn)

        self._break_btn = QPushButton("START BREAK")
        self._break_btn.setStyleSheet(theme.start_button_style(self._font_family))
        self._break_btn.clicked.connect(self._integration.start_break)
        row1.addWidget(self._break_btn)

        self._btn_layout.addLayout(row1)

        # Row 2: skip break link
        self._skip_break_btn = QPushButton("Skip Break")
        self._skip_break_btn.setStyleSheet(theme.link_button_style())
        self._skip_break_btn.clicked.connect(self._integration.skip_break)
        self._btn_layout.addWidget(self._skip_break_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._btn_container)

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 4, 0, 0)

        self._today_label = QLabel("Today: 0 pomodoros")
        self._today_label.setStyleSheet(
            f"color: {theme.COLORS['text_muted']}; font-size: 8pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        footer.addWidget(self._today_label)
        footer.addStretch()

        settings_btn = QPushButton("\u2699")
        settings_btn.setStyleSheet(theme.icon_button_style())
        settings_btn.setFixedSize(28, 28)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        footer.addWidget(settings_btn)

        stats_btn = QPushButton("\U0001F4CA")
        stats_btn.setStyleSheet(theme.icon_button_style())
        stats_btn.setFixedSize(28, 28)
        stats_btn.setToolTip("Statistics")
        stats_btn.clicked.connect(lambda: self._stack.setCurrentIndex(2))
        footer.addWidget(stats_btn)

        layout.addLayout(footer)

        self._stack.addWidget(page)

    # -- Settings View --

    def _build_settings_view(self) -> None:
        page = QWidget()
        page.setObjectName("pomo_settings_page")
        page.setStyleSheet(theme.settings_page_style(self._font_family))
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet(
            f"color: {theme.COLORS['accent']}; font-weight: bold; font-size: 12pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        layout.addWidget(title)

        # Duration sliders
        s = self._integration._settings
        self._work_slider, work_row = self._make_slider(
            "Work", s.get("work_duration_minutes", 25), 5, 60, "m"
        )
        layout.addLayout(work_row)

        self._short_slider, short_row = self._make_slider(
            "Short Break", s.get("short_break_minutes", 5), 1, 15, "m"
        )
        layout.addLayout(short_row)

        self._long_slider, long_row = self._make_slider(
            "Long Break", s.get("long_break_minutes", 15), 5, 45, "m"
        )
        layout.addLayout(long_row)

        # Checkboxes
        self._auto_start_check = QCheckBox("Auto-start next session")
        self._auto_start_check.setChecked(s.get("auto_start", False))
        layout.addWidget(self._auto_start_check)

        self._sound_check = QCheckBox("Sound effects")
        self._sound_check.setChecked(s.get("sound_enabled", True))
        layout.addWidget(self._sound_check)

        layout.addStretch()

        # Footer buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(theme.ok_button_style(self._font_family))
        ok_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(theme.cancel_button_style(self._font_family))
        cancel_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self._stack.addWidget(page)

    def _make_slider(
        self, label: str, value: int, min_val: int, max_val: int, suffix: str
    ) -> tuple[QSlider, QHBoxLayout]:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {theme.COLORS['text']}; font-size: 9pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        lbl.setFixedWidth(80)
        row.addWidget(lbl)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(value)
        row.addWidget(slider)

        val_lbl = QLabel(f"{value}{suffix}")
        val_lbl.setStyleSheet(
            f"color: {theme.COLORS['accent']}; font-size: 9pt; font-weight: bold;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        val_lbl.setFixedWidth(30)
        slider.valueChanged.connect(lambda v: val_lbl.setText(f"{v}{suffix}"))
        row.addWidget(val_lbl)

        return slider, row

    def _save_settings(self) -> None:
        """Save settings from the settings view."""
        s = self._integration._settings
        s["work_duration_minutes"] = self._work_slider.value()
        s["short_break_minutes"] = self._short_slider.value()
        s["long_break_minutes"] = self._long_slider.value()
        s["auto_start"] = self._auto_start_check.isChecked()
        s["sound_enabled"] = self._sound_check.isChecked()

        # Persist to settings.json
        all_settings = load_settings()
        all_settings.setdefault("integrations", {})["pomodoro"] = s
        save_settings(all_settings)

        # Update diamond count if sessions_per_cycle changed
        spc = s.get("sessions_per_cycle", 4)
        self._diamonds.set_count(spc)

        self._stack.setCurrentIndex(0)

    # -- Stats View --

    def _build_stats_view(self) -> None:
        page = QWidget()
        page.setStyleSheet(theme.timer_page_style())
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title = QLabel("QUEST LOG")
        title.setStyleSheet(
            f"color: {theme.COLORS['accent']}; font-weight: bold; font-size: 12pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Streak
        self._streak_label = QLabel("Streak: 0 days")
        self._streak_label.setStyleSheet(
            f"color: {theme.COLORS['text']}; font-size: 11pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        self._streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._streak_label)

        # Weekly chart
        chart_label = QLabel("This Week")
        chart_label.setStyleSheet(
            f"color: {theme.COLORS['text_muted']}; font-size: 9pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(chart_label)

        self._chart = WeeklyChart()
        layout.addWidget(self._chart)

        # Stats summary
        self._total_label = QLabel("Total: 0 sessions")
        self._total_label.setStyleSheet(
            f"color: {theme.COLORS['text']}; font-size: 9pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        self._total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._total_label)

        self._best_label = QLabel("Best day: 0 sessions")
        self._best_label.setStyleSheet(
            f"color: {theme.COLORS['text']}; font-size: 9pt;"
            f"font-family: '{self._font_family}'; background: transparent;"
        )
        self._best_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._best_label)

        layout.addStretch()

        back_btn = QPushButton("Back")
        back_btn.setStyleSheet(theme.back_button_style(self._font_family))
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._stack.addWidget(page)

    # -- Signal handlers --

    def _on_tick(self, remaining: int) -> None:
        minutes, seconds = divmod(max(remaining, 0), 60)
        self._countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
        if self._total_seconds > 0:
            self._ring.set_progress(remaining / self._total_seconds)

    def _on_state_changed(self, state_name: str, context: dict) -> None:
        self._update_button_visibility(state_name)

        if state_name == "FOCUS":
            work_min = self._integration._settings.get("work_duration_minutes", 25)
            self._total_seconds = work_min * 60
            self._ring.set_color(QColor(theme.COLORS["ring_focus"]))
            self._ring.set_progress(1.0)
            self._countdown_label.setText(f"{work_min:02d}:00")
            self._phase_label.setText("FOCUSING...")
            self._phase_label.setStyleSheet(
                f"color: {theme.COLORS['ring_focus']}; font-size: 10pt; font-weight: bold;"
                f"font-family: '{self._font_family}'; background: transparent;"
            )
        elif state_name == "SESSION_COMPLETE":
            self._ring.set_progress(0.0)
            self._countdown_label.setText("00:00")
            self._phase_label.setText("SESSION CLEAR!")
            self._phase_label.setStyleSheet(
                f"color: {theme.COLORS['accent']}; font-size: 10pt; font-weight: bold;"
                f"font-family: '{self._font_family}'; background: transparent;"
            )
        elif state_name in ("SHORT_BREAK", "LONG_BREAK"):
            if state_name == "SHORT_BREAK":
                break_min = self._integration._settings.get("short_break_minutes", 5)
            else:
                break_min = self._integration._settings.get("long_break_minutes", 15)
            self._total_seconds = break_min * 60
            self._ring.set_color(QColor(theme.COLORS["ring_break"]))
            self._ring.set_progress(1.0)
            self._countdown_label.setText(f"{break_min:02d}:00")
            self._phase_label.setText("RESTING...")
            self._phase_label.setStyleSheet(
                f"color: {theme.COLORS['ring_break']}; font-size: 10pt; font-weight: bold;"
                f"font-family: '{self._font_family}'; background: transparent;"
            )
        elif state_name == "IDLE":
            self._total_seconds = 0
            self._ring.set_color(QColor(theme.COLORS["ring_focus"]))
            self._ring.set_progress(1.0)
            self._countdown_label.setText("00:00")
            self._phase_label.setText("Ready to focus?")
            self._phase_label.setStyleSheet(
                f"color: {theme.COLORS['text_muted']}; font-size: 10pt;"
                f"font-family: '{self._font_family}'; background: transparent;"
            )

    def _on_session_completed(self, completed: int) -> None:
        self._diamonds.set_filled(completed)

    def _on_stats_updated(self, stats: dict) -> None:
        daily = stats.get("daily", {})
        today_count = daily.get(date.today().isoformat(), 0)
        self._today_label.setText(f"Today: {today_count} pomodoros")

        streak = stats.get("current_streak_days", 0)
        self._streak_label.setText(f"Streak: {streak} days")

        total = stats.get("total_sessions", 0)
        self._total_label.setText(f"Total: {total} sessions")

        best = max(daily.values(), default=0) if daily else 0
        self._best_label.setText(f"Best day: {best} sessions")

        self._chart.set_data(daily)

    def _on_pause_clicked(self) -> None:
        self._integration.pause()
        if self._integration._paused:
            self._pause_btn.setText("RESUME")
        else:
            self._pause_btn.setText("PAUSE")

    def _update_button_visibility(self, state: str) -> None:
        """Show/hide buttons based on current state."""
        self._start_btn.setVisible(state == "IDLE")
        self._pause_btn.setVisible(state in ("FOCUS", "SHORT_BREAK", "LONG_BREAK"))
        self._skip_btn.setVisible(state in ("FOCUS", "SHORT_BREAK", "LONG_BREAK"))
        self._break_btn.setVisible(state == "SESSION_COMPLETE")
        self._skip_break_btn.setVisible(state == "SESSION_COMPLETE")

        if state in ("FOCUS", "SHORT_BREAK", "LONG_BREAK"):
            self._pause_btn.setText("PAUSE")

    # -- Drag support --

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_position:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_position = None

    # -- Paint --

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw rounded rectangle background
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setPen(QPen(QColor(theme.COLORS["border"]), 1))
        painter.setBrush(QColor(theme.COLORS["bg"]))
        painter.drawRoundedRect(rect, 16, 16)
        painter.end()

    # -- Font --

    def _load_font(self) -> str:
        return theme.load_font()
