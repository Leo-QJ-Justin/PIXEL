"""Reusable widget factories for the settings dialog."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from . import theme

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _label(text: str, font: str, width: int = 120) -> QLabel:
    """Create a styled QLabel with fixed width and muted text color."""
    lbl = QLabel(text)
    lbl.setFixedWidth(width)
    lbl.setStyleSheet(
        f"color: {theme.COLORS['text_muted']}; font-family: '{font}'; font-size: 13px;"
    )
    return lbl


# ---------------------------------------------------------------------------
# make_form_row
# ---------------------------------------------------------------------------


def make_form_row(
    label_text: str,
    widget: QWidget,
    layout: QVBoxLayout,
    font: str,
    label_width: int = 120,
) -> None:
    """Add a horizontal row (label + widget) to a QVBoxLayout.

    Args:
        label_text: Text for the left-side label.
        widget: The right-side widget (stretches to fill remaining space).
        layout: Parent QVBoxLayout to append the row to.
        font: Font family string for the label.
        label_width: Fixed width for the label (default 120).
    """
    row = QHBoxLayout()
    row.setSpacing(12)

    lbl = _label(label_text, font, width=label_width)
    row.addWidget(lbl)
    row.addWidget(widget, stretch=1)

    layout.addLayout(row)


# ---------------------------------------------------------------------------
# make_slider_row
# ---------------------------------------------------------------------------


def make_slider_row(
    *,
    label: str,
    minimum: int,
    maximum: int,
    value: int,
    font: str,
    suffix: str = "",
    on_changed: Callable[[int], None] | None = None,
    label_width: int = 120,
    value_width: int = 60,
) -> tuple[QHBoxLayout, Callable[[], int]]:
    """Create a label + QSlider + live value display row.

    All parameters are keyword-only.

    Args:
        label: Left-side label text.
        minimum: Slider minimum value.
        maximum: Slider maximum value.
        value: Initial slider value.
        font: Font family string.
        suffix: String appended to the value display (e.g. " ms").
        on_changed: Optional callback called with the new int value on change.
        label_width: Fixed width for the label.
        value_width: Fixed width for the value display label.

    Returns:
        (layout, get_value_fn) where get_value_fn() returns the current int value.
    """
    row = QHBoxLayout()
    row.setSpacing(12)

    lbl = _label(label, font, width=label_width)

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setMinimum(minimum)
    slider.setMaximum(maximum)
    slider.setValue(value)

    value_lbl = QLabel(f"{value}{suffix}")
    value_lbl.setFixedWidth(value_width)
    value_lbl.setStyleSheet(
        f"color: {theme.COLORS['text_muted']}; font-family: '{font}'; font-size: 13px;"
    )
    value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _on_value_changed(v: int) -> None:
        value_lbl.setText(f"{v}{suffix}")
        if on_changed is not None:
            on_changed(v)

    slider.valueChanged.connect(_on_value_changed)

    row.addWidget(lbl)
    row.addWidget(slider, stretch=1)
    row.addWidget(value_lbl)

    def get_value() -> int:
        return slider.value()

    return row, get_value


# ---------------------------------------------------------------------------
# CollapsibleSection
# ---------------------------------------------------------------------------


class CollapsibleSection(QWidget):
    """A section card with a clickable header that toggles content visibility."""

    def __init__(self, title: str, font: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setObjectName("sectionBox")
        self.setStyleSheet(theme.section_style())

        self._expanded = True

        # --- Outer layout ---
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        # --- Header row ---
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self._arrow = QLabel("▼")
        self._arrow.setStyleSheet(
            f"color: {theme.COLORS['primary']}; font-size: 13px; font-family: '{font}';"
        )

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            f"color: {theme.COLORS['foreground']}; font-family: '{font}'; "
            f"font-size: 14px; font-weight: bold; "
            f"border-bottom: 2px solid {theme.COLORS['border']};"
        )
        self._title_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self._title_lbl.mousePressEvent = lambda _event: self.toggle()  # type: ignore[method-assign]

        header_row.addWidget(self._arrow)
        header_row.addWidget(self._title_lbl, stretch=1)

        outer.addLayout(header_row)

        # --- Content container ---
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)

        outer.addWidget(self._content)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def content_layout(self) -> QVBoxLayout:
        """Return the QVBoxLayout inside the content area."""
        return self._content_layout

    def is_expanded(self) -> bool:
        """Return True if the section is currently expanded."""
        return self._expanded

    def toggle(self) -> None:
        """Toggle the visibility of the content widget and update the arrow."""
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._arrow.setText("▼" if self._expanded else "▶")


# ---------------------------------------------------------------------------
# make_tab_page
# ---------------------------------------------------------------------------


def make_tab_page(font: str) -> tuple[QWidget, QVBoxLayout]:
    """Create a styled tab page widget.

    Args:
        font: Font family string applied via content_style QSS.

    Returns:
        (page_widget, layout) where layout is the page's QVBoxLayout.
    """
    page = QWidget()
    page.setStyleSheet(
        f"background-color: {theme.COLORS['background']};" + theme.content_style(font)
    )

    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(16)

    return page, layout
