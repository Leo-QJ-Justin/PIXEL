"""Stats surface page — calendar heat map, stat cards, mood trend, prompt widget."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from integrations.journal.widgets.calendar_map import CalendarMap

# Mood emoji → bar height mapping (0.0 to 1.0)
MOOD_HEIGHTS = {"😊": 1.0, "🙂": 0.75, "😐": 0.5, "😔": 0.3, "😢": 0.15}


class _MoodTrendWidget(QWidget):
    """Small bar chart showing mood values for the last 7 days."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[dict] = []
        self.setFixedHeight(80)
        self.setStyleSheet(
            "background: rgba(22,22,46,0.8); border-radius: 12px; border: 1px solid rgba(30,30,58,0.8);"
        )

    def set_data(self, data: list[dict]) -> None:
        self._data = data[-7:]  # last 7 entries with mood
        self.update()

    def paintEvent(self, event) -> None:
        from PyQt6.QtGui import QColor, QPainter

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._data:
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No mood data yet")
            painter.end()
            return

        w = self.width()
        h = self.height()
        bar_w = max(8, (w - 40) // max(len(self._data), 1))
        start_x = (w - bar_w * len(self._data)) // 2
        max_h = h - 30

        for i, entry in enumerate(self._data):
            mood = entry.get("mood", "😐")
            height_pct = MOOD_HEIGHTS.get(mood, 0.5)
            bar_h = int(max_h * height_pct)
            x = start_x + i * bar_w
            y = h - 15 - bar_h

            color = QColor(45, 90, 60) if height_pct > 0.5 else QColor(90, 60, 45)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x + 2, y, bar_w - 4, bar_h, 3, 3)

        painter.end()


class StatsSurface(QWidget):
    """Default dashboard page showing journaling stats (no text content)."""

    open_vault_clicked = pyqtSignal()
    write_prompt_clicked = pyqtSignal(str)  # prompt text
    date_clicked = pyqtSignal(str)  # ISO date

    def __init__(self, integration, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._integration = integration
        self._store = integration._get_store()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Calendar heat map
        self._calendar = CalendarMap()
        self._calendar.date_clicked.connect(self.date_clicked)
        layout.addWidget(self._calendar)

        # Stats cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self._streak_card = self._make_stat_card("Current Streak", "0", "days")
        self._month_card = self._make_stat_card("This Month", "0", "entries")
        self._total_card = self._make_stat_card("Total", "0", "entries")

        cards_row.addWidget(self._streak_card)
        cards_row.addWidget(self._month_card)
        cards_row.addWidget(self._total_card)
        layout.addLayout(cards_row)

        # Mood trend bar chart
        self._mood_trend = _MoodTrendWidget()
        layout.addWidget(self._mood_trend)

        # Prompt widget
        prompt_widget = self._build_prompt_widget()
        layout.addWidget(prompt_widget)

        # Open Vault button
        vault_btn = QPushButton("📖 Open Vault")
        vault_btn.setStyleSheet(
            """
            QPushButton {
                padding: 10px 24px;
                border-radius: 8px;
                background: rgba(102,170,187,0.15);
                border: 1px solid rgba(102,170,187,0.3);
                color: #6ab;
                font-size: 13px;
            }
            QPushButton:hover { background: rgba(102,170,187,0.25); }
        """
        )
        vault_btn.clicked.connect(self.open_vault_clicked)
        layout.addWidget(vault_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        self.refresh()

    def _make_stat_card(self, title: str, value: str, unit: str) -> QWidget:
        card = QWidget()
        card.setStyleSheet(
            """
            QWidget {
                background: rgba(22,22,46,0.8);
                border-radius: 12px;
                border: 1px solid rgba(30,30,58,0.8);
                padding: 16px;
            }
        """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "color: #666; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; border: none; background: transparent;"
        )
        layout.addWidget(title_label)

        value_row = QHBoxLayout()
        value_label = QLabel(value)
        value_label.setObjectName("stat_value")
        value_label.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #6fcf97; border: none; background: transparent;"
        )
        value_row.addWidget(value_label)

        unit_label = QLabel(unit)
        unit_label.setStyleSheet(
            "font-size: 12px; color: #888; border: none; background: transparent;"
        )
        unit_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        value_row.addWidget(unit_label)
        value_row.addStretch()

        layout.addLayout(value_row)
        return card

    def _build_prompt_widget(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(26,26,58,0.8), stop:1 rgba(30,42,58,0.8));
                border-radius: 12px;
                border: 1px solid rgba(42,58,90,0.8);
            }
        """
        )
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        pet_icon = QLabel("🐾")
        pet_icon.setFixedSize(48, 48)
        pet_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pet_icon.setStyleSheet(
            "font-size: 24px; background: rgba(42,42,74,0.8); border-radius: 24px; border: none;"
        )
        layout.addWidget(pet_icon)

        text_col = QVBoxLayout()
        label = QLabel("Haro says...")
        label.setStyleSheet("color: #6ab; font-size: 12px; border: none; background: transparent;")
        text_col.addWidget(label)

        prompt = self._integration.get_daily_prompt()
        self._prompt_label = QLabel(f'"{prompt}"')
        self._prompt_label.setWordWrap(True)
        self._prompt_label.setStyleSheet(
            "color: #ccc; font-size: 13px; border: none; background: transparent;"
        )
        text_col.addWidget(self._prompt_label)
        layout.addLayout(text_col, stretch=1)

        write_btn = QPushButton("Write about it →")
        write_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(26,42,77,0.8);
                border: 1px solid rgba(42,58,93,0.8);
                border-radius: 8px;
                padding: 6px 14px;
                color: #6ab;
                font-size: 11px;
            }
            QPushButton:hover { background: rgba(42,58,93,0.8); }
        """
        )
        write_btn.clicked.connect(lambda: self.write_prompt_clicked.emit(prompt))
        layout.addWidget(write_btn)

        return widget

    def refresh(self) -> None:
        """Refresh all stats from the store."""
        store = self._store

        # Update calendar
        year, month = self._calendar.current_year, self._calendar.current_month
        entries = store.get_entries_for_month(year, month)
        entry_dates = {e["date"] for e in entries}
        self._calendar.set_entry_dates(entry_dates)

        # Update stat cards
        current_streak, best_streak = store.get_streak()
        month_count = len(entries)
        total = store.get_total_count()

        self._streak_card.findChild(QLabel, "stat_value").setText(str(current_streak))
        self._month_card.findChild(QLabel, "stat_value").setText(str(month_count))
        self._total_card.findChild(QLabel, "stat_value").setText(str(total))

        # Update mood trend
        mood_data = store.get_mood_trend(7)
        self._mood_trend.set_data(mood_data)
