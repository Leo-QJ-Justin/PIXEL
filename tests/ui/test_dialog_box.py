"""Tests for MapleStory-style DialogBox and MapleButton widgets."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

# Required for patching — see MEMORY.md gotcha about Python 3.14 mock.patch
import src.ui.dialog_box  # noqa: F401
from src.ui.dialog_box import DialogBox, MapleButton, draw_nine_slice


@pytest.mark.ui
class TestDrawNineSlice:
    """Tests for the 9-slice drawing utility."""

    def test_does_not_crash_with_null_pixmap(self, qtbot):
        from PyQt6.QtCore import QRect
        from PyQt6.QtGui import QImage, QPainter

        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        painter = QPainter(img)
        draw_nine_slice(painter, QPixmap(), QRect(0, 0, 100, 100), 10, 10, 10, 10)
        painter.end()

    def test_draws_with_valid_pixmap(self, qtbot):
        from PyQt6.QtCore import QRect
        from PyQt6.QtGui import QImage, QPainter

        # Create a small test pixmap
        src = QPixmap(40, 40)
        src.fill(Qt.GlobalColor.blue)

        img = QImage(200, 200, QImage.Format.Format_ARGB32)
        painter = QPainter(img)
        draw_nine_slice(painter, src, QRect(0, 0, 200, 200), 10, 10, 10, 10)
        painter.end()
        # If we get here without crash, the function works


@pytest.mark.ui
class TestMapleButton:
    """Tests for MapleButton widget."""

    def test_creates_with_text(self, qtbot):
        sprite = QPixmap(100, 40)
        sprite.fill(Qt.GlobalColor.yellow)
        btn = MapleButton("OK", sprite)
        qtbot.addWidget(btn)
        assert btn.text() == "OK"

    def test_has_pointing_hand_cursor(self, qtbot):
        sprite = QPixmap(100, 40)
        sprite.fill(Qt.GlobalColor.yellow)
        btn = MapleButton("OK", sprite)
        qtbot.addWidget(btn)
        assert btn.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_fixed_height(self, qtbot):
        sprite = QPixmap(100, 40)
        sprite.fill(Qt.GlobalColor.yellow)
        btn = MapleButton("OK", sprite)
        qtbot.addWidget(btn)
        assert btn.height() == 36

    def test_minimum_width(self, qtbot):
        sprite = QPixmap(100, 40)
        sprite.fill(Qt.GlobalColor.yellow)
        btn = MapleButton("OK", sprite)
        qtbot.addWidget(btn)
        assert btn.width() >= 90


@pytest.mark.ui
class TestDialogBoxInit:
    """Tests for DialogBox initialization."""

    def test_creates_without_error(self, qtbot):
        dialog = DialogBox(title="Test")
        qtbot.addWidget(dialog)
        assert dialog is not None

    def test_stores_title(self, qtbot):
        dialog = DialogBox(title="My Title")
        qtbot.addWidget(dialog)
        assert dialog._title == "My Title"

    def test_has_frameless_flag(self, qtbot):
        dialog = DialogBox(title="Test")
        qtbot.addWidget(dialog)
        assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint

    def test_has_stay_on_top_flag(self, qtbot):
        dialog = DialogBox(title="Test")
        qtbot.addWidget(dialog)
        assert dialog.windowFlags() & Qt.WindowType.WindowStaysOnTopHint

    def test_has_translucent_background(self, qtbot):
        dialog = DialogBox(title="Test")
        qtbot.addWidget(dialog)
        assert dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def test_is_application_modal(self, qtbot):
        dialog = DialogBox(title="Test")
        qtbot.addWidget(dialog)
        assert dialog.windowModality() == Qt.WindowModality.ApplicationModal

    def test_default_ok_button(self, qtbot):
        dialog = DialogBox(title="Test")
        qtbot.addWidget(dialog)
        # Should have one MapleButton with "OK" text
        buttons = dialog.findChildren(MapleButton)
        assert len(buttons) == 1
        assert buttons[0].text() == "OK"

    def test_custom_buttons(self, qtbot):
        dialog = DialogBox(
            title="Test",
            buttons=[("Yes", "accept"), ("No", "reject")],
        )
        qtbot.addWidget(dialog)
        buttons = dialog.findChildren(MapleButton)
        assert len(buttons) == 2
        labels = {b.text() for b in buttons}
        assert labels == {"Yes", "No"}


@pytest.mark.ui
class TestDialogBoxContent:
    """Tests for body text and form content."""

    def test_set_body_html(self, qtbot):
        dialog = DialogBox(title="Test", body_text="Initial")
        qtbot.addWidget(dialog)
        dialog.set_body_html("<b>Bold</b> text")
        assert "<b>Bold</b>" in dialog._body_label.text()

    def test_add_form_row(self, qtbot):
        from PyQt6.QtWidgets import QLineEdit

        dialog = DialogBox(title="Test")
        qtbot.addWidget(dialog)
        edit = QLineEdit()
        dialog.add_form_row("Name:", edit)
        # Form widget is not hidden (show() was called), even though
        # parent dialog isn't shown so isVisible() would be False
        assert not dialog._form_widget.isHidden()

    def test_multiple_form_rows(self, qtbot):
        from PyQt6.QtWidgets import QLineEdit

        dialog = DialogBox(title="Test")
        qtbot.addWidget(dialog)
        dialog.add_form_row("A:", QLineEdit())
        dialog.add_form_row("B:", QLineEdit())
        assert dialog._form_layout.count() == 2

    def test_portrait_stored(self, qtbot):
        portrait = QPixmap(64, 64)
        portrait.fill(Qt.GlobalColor.green)
        dialog = DialogBox(title="Test", portrait_pixmap=portrait)
        qtbot.addWidget(dialog)
        assert dialog._portrait is not None
        assert not dialog._portrait.isNull()

    def test_no_portrait_by_default(self, qtbot):
        dialog = DialogBox(title="Test")
        qtbot.addWidget(dialog)
        assert dialog._portrait is None
