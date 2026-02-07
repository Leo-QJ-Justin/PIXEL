"""Tests for SpeechBubble widget."""


import pytest
from PyQt6.QtCore import QPoint, QSize, Qt

from src.ui.speech_bubble import SpeechBubble


@pytest.mark.ui
class TestSpeechBubbleInit:
    """Tests for SpeechBubble initialization."""

    def test_creates_without_error(self, qtbot):
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        assert bubble is not None

    def test_starts_hidden(self, qtbot):
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        assert not bubble.isVisible()

    def test_has_frameless_flag(self, qtbot):
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        assert bubble.windowFlags() & Qt.WindowType.FramelessWindowHint

    def test_has_tool_flag(self, qtbot):
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        assert bubble.windowFlags() & Qt.WindowType.Tool


@pytest.mark.ui
class TestSpeechBubbleShowHide:
    """Tests for showing and hiding the speech bubble."""

    def test_show_message_makes_visible(self, qtbot):
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        bubble._pet_pos = QPoint(100, 100)
        bubble._pet_size = QSize(100, 100)
        bubble.show_message("Hello!")
        assert bubble.isVisible()

    def test_show_message_stores_text(self, qtbot):
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        bubble._pet_pos = QPoint(100, 100)
        bubble._pet_size = QSize(100, 100)
        bubble.show_message("Hello!")
        assert bubble._text == "Hello!"

    def test_hide_bubble_hides(self, qtbot):
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        bubble._pet_pos = QPoint(100, 100)
        bubble._pet_size = QSize(100, 100)
        bubble.show_message("Hello!")
        bubble.hide_bubble()
        assert not bubble.isVisible()

    def test_hide_bubble_stops_timer(self, qtbot):
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        bubble._pet_pos = QPoint(100, 100)
        bubble._pet_size = QSize(100, 100)
        bubble.show_message("Hello!", duration_ms=5000)
        bubble.hide_bubble()
        assert not bubble._dismiss_timer.isActive()


@pytest.mark.ui
class TestSpeechBubblePositioning:
    """Tests for bubble positioning logic."""

    def test_update_position_stores_values(self, qtbot):
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        pos = QPoint(200, 300)
        size = QSize(100, 100)
        bubble.update_position(pos, size)
        assert bubble._pet_pos == pos
        assert bubble._pet_size == size

    def test_tail_on_left_by_default(self, qtbot):
        """Bubble to the right of pet means tail points left."""
        bubble = SpeechBubble()
        qtbot.addWidget(bubble)
        bubble._pet_pos = QPoint(100, 100)
        bubble._pet_size = QSize(100, 100)
        bubble.show_message("Test")
        assert bubble._tail_on_left is True
