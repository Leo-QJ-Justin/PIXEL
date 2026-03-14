"""Entry editor page — mode picker, paper-style editor, mood picker, cleanup."""

from __future__ import annotations

import asyncio
import logging
from datetime import date

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from integrations.journal.widgets.mood_picker import MoodPicker

logger = logging.getLogger(__name__)


class LinedTextEdit(QTextEdit):
    """QTextEdit with horizontal ruled lines painted behind the text."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            """
            QTextEdit {
                background: #2a2520;
                color: #e0d8d0;
                border: none;
                padding: 12px 16px;
                font-size: 14px;
                line-height: 1.8;
            }
        """
        )
        font = QFont("Georgia", 13)
        font.setStyleHint(QFont.StyleHint.Serif)
        self.setFont(font)

    def paintEvent(self, event) -> None:
        # Draw ruled lines
        painter = QPainter(self.viewport())
        painter.setPen(QPen(QColor(60, 55, 50), 0.5))

        font_metrics = self.fontMetrics()
        line_height = font_metrics.lineSpacing()
        if line_height < 10:
            line_height = 28

        # Start lines from the top of the document, offset by content margins
        doc_margin = int(self.document().documentMargin())
        scroll_offset = self.verticalScrollBar().value()

        viewport_height = self.viewport().height()

        # Start at first visible line
        y = doc_margin - (scroll_offset % line_height) + line_height
        while y < viewport_height:
            painter.drawLine(0, int(y), self.viewport().width(), int(y))
            y += line_height

        painter.end()

        # Then draw text on top
        super().paintEvent(event)


class EntryEditor(QWidget):
    """Journal entry editor with mode picker, paper-style text, and cleanup."""

    entry_saved = pyqtSignal(str, str)  # date, mood
    back_requested = pyqtSignal()

    def __init__(self, integration, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._integration = integration
        self._store = integration._get_store()
        self._current_date: str = ""
        self._current_mode: str = ""
        self._autosave_timer = QTimer()
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(3000)
        self._autosave_timer.timeout.connect(self._autosave)

        self._build_ui()

    def _build_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)

        # Mode picker (shown initially, hidden after selection)
        self._mode_picker = self._build_mode_picker()
        self._layout.addWidget(self._mode_picker)

        # Editor area (hidden initially)
        self._editor_area = QWidget()
        editor_layout = QVBoxLayout(self._editor_area)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(8)

        # Date header
        self._date_label = QLabel()
        self._date_label.setStyleSheet("color: #6ab; font-size: 14px; font-weight: bold;")
        editor_layout.addWidget(self._date_label)

        # Prompt display (for guided mode)
        self._prompt_label = QLabel()
        self._prompt_label.setWordWrap(True)
        self._prompt_label.setStyleSheet(
            """
            color: #aaa; font-style: italic; font-size: 13px;
            padding: 8px 12px; background: rgba(102,170,187,0.08);
            border-radius: 6px; border-left: 3px solid #6ab;
        """
        )
        self._prompt_label.setVisible(False)
        editor_layout.addWidget(self._prompt_label)

        # Mood picker
        self._mood_picker = MoodPicker()
        editor_layout.addWidget(self._mood_picker)

        # Paper-style text editor
        self._text_edit = LinedTextEdit()
        self._text_edit.textChanged.connect(self._on_text_changed)
        editor_layout.addWidget(self._text_edit, stretch=1)

        # Bottom bar: cleanup button + save status
        bottom = QHBoxLayout()

        self._cleanup_btn = QPushButton("✨ Clean up")
        self._cleanup_btn.setStyleSheet(
            """
            QPushButton {
                padding: 6px 16px; border-radius: 6px;
                background: rgba(102,170,187,0.15);
                border: 1px solid rgba(102,170,187,0.3);
                color: #6ab; font-size: 12px;
            }
            QPushButton:hover { background: rgba(102,170,187,0.25); }
        """
        )
        self._cleanup_btn.clicked.connect(self._on_cleanup)
        bottom.addWidget(self._cleanup_btn)

        self._status_label = QLabel()
        self._status_label.setStyleSheet("color: #666; font-size: 11px;")
        bottom.addWidget(self._status_label)
        bottom.addStretch()

        # View toggle (My words / Polished)
        self._toggle_btn = QPushButton("Show polished")
        self._toggle_btn.setVisible(False)
        self._toggle_btn.setStyleSheet(
            """
            QPushButton {
                padding: 4px 12px; border-radius: 4px;
                background: transparent; border: 1px solid #444;
                color: #888; font-size: 11px;
            }
        """
        )
        self._toggle_btn.clicked.connect(self._toggle_view)
        bottom.addWidget(self._toggle_btn)

        editor_layout.addLayout(bottom)

        self._editor_area.setVisible(False)
        self._layout.addWidget(self._editor_area, stretch=1)

        self._showing_clean = False

    def _build_mode_picker(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        title = QLabel("What kind of entry?")
        title.setStyleSheet("color: #e0e0e0; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        modes = [
            ("✏️ Free Write", "freeform", "Write whatever comes to mind"),
            ("💭 Guided Reflection", "guided", "Start with a prompt from PIXEL"),
            ("😊 Quick Mood", "mood", "Log how you're feeling"),
        ]

        for emoji_title, mode, desc in modes:
            btn = QPushButton()
            btn.setStyleSheet(
                """
                QPushButton {
                    text-align: left; padding: 16px 20px;
                    border-radius: 10px; background: rgba(22,22,46,0.8);
                    border: 1px solid rgba(30,30,58,0.8); color: #ccc;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: rgba(30,30,58,0.9);
                    border-color: rgba(102,170,187,0.4);
                }
            """
            )
            btn.setText(f"{emoji_title}\n{desc}")
            btn.clicked.connect(lambda checked, m=mode: self._select_mode(m))
            layout.addWidget(btn)

        layout.addStretch()
        return widget

    def open_new_entry(self, mode: str | None = None, prompt: str | None = None) -> None:
        """Open editor for a new entry on today's date."""
        self._current_date = date.today().isoformat()
        if mode:
            self._select_mode(mode, prompt)
        else:
            self._mode_picker.setVisible(True)
            self._editor_area.setVisible(False)

    def open_existing_entry(self, date_str: str) -> None:
        """Open an existing entry for viewing/editing."""
        self._current_date = date_str
        entry = self._store.get_entry(date_str)
        if entry:
            self._current_mode = entry["mode"]
            self._show_editor(entry["mode"])
            self._text_edit.setPlainText(entry["raw_text"])
            self._mood_picker.set_mood(entry.get("mood"))
            if entry.get("prompt_used"):
                self._prompt_label.setText(f'"{entry["prompt_used"]}"')
                self._prompt_label.setVisible(True)
            if entry.get("clean_text"):
                self._toggle_btn.setVisible(True)
        else:
            self.open_new_entry()

    def _select_mode(self, mode: str, prompt: str | None = None) -> None:
        self._current_mode = mode
        self._show_editor(mode, prompt)

    def _show_editor(self, mode: str, prompt: str | None = None) -> None:
        self._mode_picker.setVisible(False)
        self._editor_area.setVisible(True)
        self._text_edit.clear()
        self._toggle_btn.setVisible(False)
        self._showing_clean = False
        self._status_label.clear()

        # Set date header
        from datetime import datetime

        try:
            dt = datetime.fromisoformat(self._current_date)
            self._date_label.setText(dt.strftime("%A, %B %d, %Y").replace(" 0", " "))
        except ValueError:
            self._date_label.setText(self._current_date)

        # Mode-specific setup
        if mode == "guided":
            p = prompt or self._integration.get_daily_prompt(self._current_date)
            self._prompt_label.setText(f'"{p}"')
            self._prompt_label.setVisible(True)
        else:
            self._prompt_label.setVisible(False)

        self._text_edit.setFocus()

    def emit_save(self) -> None:
        """Emit entry_saved signal (called when navigating away from editor)."""
        if self._current_date and self._text_edit.toPlainText().strip():
            self.entry_saved.emit(self._current_date, self._mood_picker.selected_mood or "")

    def _on_text_changed(self) -> None:
        self._autosave_timer.start()

    def _autosave(self) -> None:
        """Save entry silently (no pet reactions — those happen on explicit save/close)."""
        text = self._text_edit.toPlainText().strip()
        if not text or not self._current_date:
            return
        # Preserve existing clean_text if any
        existing = self._store.get_entry(self._current_date)
        existing_clean = existing["clean_text"] if existing else None
        prompt = self._prompt_label.text().strip('"') if self._prompt_label.isVisible() else None
        self._store.save_entry(
            entry_date=self._current_date,
            mode=self._current_mode,
            mood=self._mood_picker.selected_mood,
            raw_text=text,
            clean_text=existing_clean,
            prompt_used=prompt,
        )
        self._status_label.setText("Saved")

    def _on_cleanup(self) -> None:
        """Send raw text to LLM for restructuring."""
        text = self._text_edit.toPlainText().strip()
        if not text:
            return

        self._cleanup_btn.setEnabled(False)
        self._status_label.setText("Cleaning up...")

        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._do_cleanup(text))
        except RuntimeError:
            self._status_label.setText("Couldn't clean up — no event loop")
            self._cleanup_btn.setEnabled(True)

    async def _do_cleanup(self, raw_text: str) -> None:
        """Async LLM cleanup call."""
        try:
            import litellm

            from config import load_settings
            from src.services.personality_engine import PROVIDER_CONFIG

            settings = load_settings()
            pe = settings.get("personality_engine", {})
            provider = pe.get("provider", "openai")
            model = pe.get("model", "gpt-4o-mini")
            api_key = pe.get("api_key", "")
            endpoint = pe.get("endpoint", "")

            cfg = PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["custom"])
            model_string = f"{cfg['prefix']}{model}"

            kwargs = {
                "model": model_string,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Restructure the following messy journal text into clear, "
                            "readable prose. Preserve the original meaning, tone, and "
                            "all details. Do not add, remove, or editorialize content."
                        ),
                    },
                    {"role": "user", "content": raw_text},
                ],
                "max_tokens": 500,
                "temperature": 0.3,
                "timeout": 15,
            }

            if cfg.get("needs_api_key") and api_key:
                kwargs["api_key"] = api_key
            if cfg.get("needs_endpoint") and endpoint:
                kwargs["api_base"] = endpoint

            response = await litellm.acompletion(**kwargs)
            clean = response.choices[0].message.content
            if clean and clean.strip():
                clean = clean.strip()
                # Save clean text
                self._store.save_entry(
                    entry_date=self._current_date,
                    mode=self._current_mode,
                    mood=self._mood_picker.selected_mood,
                    raw_text=raw_text,
                    clean_text=clean,
                    prompt_used=self._prompt_label.text().strip('"')
                    if self._prompt_label.isVisible()
                    else None,
                )
                self._toggle_btn.setVisible(True)
                self._showing_clean = True
                self._text_edit.setPlainText(clean)
                self._toggle_btn.setText("Show my words")
                self._status_label.setText("Cleaned up and saved")
            else:
                self._status_label.setText("Couldn't clean up — empty response")
        except Exception:
            logger.debug("Journal cleanup failed", exc_info=True)
            self._status_label.setText("Couldn't clean up — check your LLM settings")
        finally:
            self._cleanup_btn.setEnabled(True)

    def _toggle_view(self) -> None:
        entry = self._store.get_entry(self._current_date)
        if not entry:
            return

        if self._showing_clean:
            self._text_edit.setPlainText(entry["raw_text"])
            self._toggle_btn.setText("Show polished")
            self._showing_clean = False
        else:
            if entry.get("clean_text"):
                self._text_edit.setPlainText(entry["clean_text"])
                self._toggle_btn.setText("Show my words")
                self._showing_clean = True
