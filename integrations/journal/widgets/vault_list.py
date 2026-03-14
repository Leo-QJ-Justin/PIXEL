"""Vault list page — date-only entry list with no text previews."""

from __future__ import annotations

from datetime import date, datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class VaultList(QWidget):
    """Shows journal entries as date-only rows."""

    entry_clicked = pyqtSignal(str)  # ISO date string
    new_entry_clicked = pyqtSignal()

    def __init__(self, store, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Journal Entries")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        header.addWidget(title)
        header.addStretch()

        new_btn = QPushButton("+ New Entry")
        new_btn.setStyleSheet(
            """
            QPushButton {
                padding: 6px 16px;
                border-radius: 6px;
                background: rgba(102,170,187,0.15);
                border: 1px solid rgba(102,170,187,0.3);
                color: #6ab;
                font-size: 12px;
            }
            QPushButton:hover { background: rgba(102,170,187,0.25); }
        """
        )
        new_btn.clicked.connect(self.new_entry_clicked)
        header.addWidget(new_btn)
        layout.addLayout(header)

        # Scrollable entry list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll)

    def refresh(self) -> None:
        """Rebuild the entry list from the store."""
        # Clear existing rows
        while self._list_layout.count() > 1:  # keep the stretch
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get recent entries by querying last 12 months
        today = date.today()
        all_entries = []
        for month_offset in range(12):
            m = today.month - month_offset
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            entries = self._store.get_entries_for_month(y, m)
            all_entries.extend(entries)

        # Sort by date descending
        all_entries.sort(key=lambda e: e["date"], reverse=True)

        # Build rows
        for entry in all_entries:
            row = self._make_entry_row(entry["date"])
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

    def _make_entry_row(self, date_str: str) -> QWidget:
        row = QWidget()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet(
            """
            QWidget {
                background: rgba(30,30,56,0.6);
                border-radius: 6px;
                padding: 8px 12px;
            }
            QWidget:hover {
                background: rgba(34,34,64,0.8);
            }
        """
        )

        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)

        try:
            dt = datetime.fromisoformat(date_str)
            display = dt.strftime("%A, %B %d").replace(" 0", " ")
        except ValueError:
            display = date_str

        date_label = QLabel(display)
        date_label.setStyleSheet("color: #aaa; font-size: 13px; background: transparent;")
        layout.addWidget(date_label)

        layout.addStretch()

        dash = QLabel("— — — — —")
        dash.setStyleSheet("color: #444; font-size: 11px; background: transparent;")
        layout.addWidget(dash)

        row.mousePressEvent = lambda event, d=date_str: self.entry_clicked.emit(d)

        return row
