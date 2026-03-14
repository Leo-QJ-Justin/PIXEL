"""Mood picker widget — row of 5 emoji buttons."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

MOODS = ["😊", "🙂", "😐", "😔", "😢"]


class MoodPicker(QWidget):
    """Row of 5 emoji buttons for selecting mood."""

    mood_selected = pyqtSignal(str)  # emits the selected emoji

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected: str | None = None
        self._buttons: dict[str, QPushButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addStretch()

        for mood in MOODS:
            btn = QPushButton(mood)
            btn.setFixedSize(40, 40)
            btn.setCheckable(True)
            btn.setStyleSheet(
                """
                QPushButton {
                    font-size: 20px;
                    border: 2px solid transparent;
                    border-radius: 20px;
                    background: rgba(255,255,255,0.05);
                }
                QPushButton:checked {
                    border-color: #6ab;
                    background: rgba(102,170,187,0.2);
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.1);
                }
            """
            )
            btn.clicked.connect(lambda checked, m=mood: self._on_click(m))
            layout.addWidget(btn)
            self._buttons[mood] = btn

        layout.addStretch()

    def _on_click(self, mood: str) -> None:
        # Deselect others
        for m, btn in self._buttons.items():
            if m != mood:
                btn.setChecked(False)

        if self._buttons[mood].isChecked():
            self._selected = mood
        else:
            self._selected = None

        self.mood_selected.emit(self._selected or "")

    @property
    def selected_mood(self) -> str | None:
        return self._selected

    def set_mood(self, mood: str | None) -> None:
        """Programmatically select a mood."""
        for m, btn in self._buttons.items():
            btn.setChecked(m == mood)
        self._selected = mood
