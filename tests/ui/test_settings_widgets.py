from PyQt6.QtWidgets import QCheckBox, QSlider, QVBoxLayout, QWidget

from src.ui.settings.widgets import (
    SectionCard,
    make_form_row,
    make_slider_row,
    make_tab_page,
)


class TestMakeSliderRow:
    def test_returns_layout_and_getter(self, qtbot):
        parent = QWidget()
        qtbot.addWidget(parent)
        layout, get_value = make_slider_row(
            label="Duration",
            minimum=0,
            maximum=10000,
            value=3000,
            suffix=" ms",
            font="sans-serif",
        )
        assert get_value() == 3000

    def test_callback_fires_on_change(self, qtbot):
        parent = QWidget()
        qtbot.addWidget(parent)
        received = []
        layout, get_value = make_slider_row(
            label="Test",
            minimum=0,
            maximum=100,
            value=50,
            suffix="%",
            font="sans-serif",
            on_changed=lambda v: received.append(v),
        )
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            if isinstance(w, QSlider):
                w.setValue(75)
                break
        assert 75 in received


class TestSectionCard:
    def test_content_layout_exists(self, qtbot):
        section = SectionCard("Test Section", font="sans-serif")
        qtbot.addWidget(section)
        assert section.content_layout() is not None

    def test_has_title(self, qtbot):
        section = SectionCard("My Title", font="sans-serif")
        qtbot.addWidget(section)
        assert section._title_lbl.text() == "My Title"


class TestMakeTabPage:
    def test_returns_widget_and_layout(self, qtbot):
        page, layout = make_tab_page(font="sans-serif")
        qtbot.addWidget(page)
        assert isinstance(page, QWidget)
        assert isinstance(layout, QVBoxLayout)


class TestMakeFormRow:
    def test_adds_row_to_layout(self, qtbot):
        parent = QWidget()
        qtbot.addWidget(parent)
        parent_layout = QVBoxLayout(parent)
        cb = QCheckBox("Test")
        make_form_row("Label", cb, parent_layout, font="sans-serif")
        assert parent_layout.count() == 1  # one row layout added
