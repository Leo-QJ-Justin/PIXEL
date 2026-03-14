"""Calendar heat map widget — shows journaling activity by month."""

from __future__ import annotations

import calendar
from datetime import date

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class CalendarMap(QWidget):
    """Custom-painted monthly calendar heat map."""

    date_clicked = pyqtSignal(str)  # ISO date string

    def __init__(self, entry_dates: set[str] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._year = date.today().year
        self._month = date.today().month
        self._entry_dates: set[str] = entry_dates or set()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Navigation header
        nav = QHBoxLayout()
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedSize(32, 32)
        self._prev_btn.clicked.connect(self._prev_month)

        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedSize(32, 32)
        self._next_btn.clicked.connect(self._next_month)

        self._month_label = QPushButton()
        self._month_label.setFlat(True)
        self._month_label.setEnabled(False)

        nav.addWidget(self._prev_btn)
        nav.addStretch()
        nav.addWidget(self._month_label)
        nav.addStretch()
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)

        # Grid area (painted)
        self._grid = _CalendarGrid(self)
        self._grid.date_clicked.connect(self.date_clicked)
        layout.addWidget(self._grid)

        self._update_label()

    def _update_label(self) -> None:
        name = calendar.month_name[self._month]
        self._month_label.setText(f"{name} {self._year}")

    def _prev_month(self) -> None:
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self._update_label()
        self._grid.set_month(self._year, self._month, self._entry_dates)

    def _next_month(self) -> None:
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self._update_label()
        self._grid.set_month(self._year, self._month, self._entry_dates)

    def set_entry_dates(self, dates: set[str]) -> None:
        """Update which dates have entries."""
        self._entry_dates = dates
        self._grid.set_month(self._year, self._month, self._entry_dates)

    @property
    def current_year(self) -> int:
        return self._year

    @property
    def current_month(self) -> int:
        return self._month


class _CalendarGrid(QWidget):
    """Inner widget that paints the calendar grid."""

    date_clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._year = date.today().year
        self._month = date.today().month
        self._entry_dates: set[str] = set()
        self._cell_rects: list[tuple[QRectF, str]] = []  # (rect, date_str)

        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_month(self, year: int, month: int, entry_dates: set[str]) -> None:
        self._year = year
        self._month = month
        self._entry_dates = entry_dates
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        col_w = w / 7
        row_h = min(30, (h - 20) / 7)  # header + up to 6 rows

        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        painter.setPen(QColor(120, 120, 120))
        header_font = QFont()
        header_font.setPointSize(9)
        painter.setFont(header_font)
        for i, day in enumerate(days):
            rect = QRectF(i * col_w, 0, col_w, 18)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, day)

        # Calendar cells
        cal = calendar.monthcalendar(self._year, self._month)
        self._cell_rects.clear()
        today = date.today()

        cell_font = QFont()
        cell_font.setPointSize(10)
        painter.setFont(cell_font)

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue

                x = col_idx * col_w
                y = 20 + row_idx * row_h
                cell = QRectF(x + 2, y + 1, col_w - 4, row_h - 2)

                date_str = f"{self._year:04d}-{self._month:02d}-{day:02d}"
                self._cell_rects.append((cell, date_str))

                # Draw cell background
                is_today = (
                    self._year == today.year and self._month == today.month and day == today.day
                )
                has_entry = date_str in self._entry_dates

                if has_entry:
                    painter.setBrush(QColor(45, 90, 60))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(cell, 4, 4)
                    painter.setPen(QColor(111, 207, 151))
                elif is_today:
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.setPen(QPen(QColor(102, 170, 187), 1.5))
                    painter.drawRoundedRect(cell, 4, 4)
                    painter.setPen(QColor(102, 170, 187))
                else:
                    painter.setPen(QColor(100, 100, 100))

                painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, str(day))

        painter.end()

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        for rect, date_str in self._cell_rects:
            if rect.contains(pos):
                self.date_clicked.emit(date_str)
                return
