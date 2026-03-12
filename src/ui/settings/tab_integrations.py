"""Integrations settings tab — discovers settings UI from each integration."""

from __future__ import annotations

import importlib
import logging

from PyQt6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from .widgets import make_tab_page

logger = logging.getLogger(__name__)

# Integration names in the order they should appear in the UI.
# Only integrations that have a settings_ui module will show up.
_INTEGRATION_ORDER = ["pomodoro", "weather", "google_calendar"]


def build_integrations_tab(pending: dict, font: str, integration_manager=None) -> QWidget:
    """Build the Integrations tab by discovering settings_ui modules.

    Each integration may provide an ``integrations/<name>/settings_ui.py``
    module that exports ``build_settings_sections(pending, font,
    integration_manager?) -> list[QWidget]``.  This function collects all
    those sections into a scrollable page.

    Args:
        pending: Mutable settings buffer dict.
        font: Font family string for styling.
        integration_manager: Optional integration manager passed through.

    Returns:
        A QWidget suitable for placement in a QStackedWidget.
    """
    page, outer_layout = make_tab_page(font)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)

    inner = QWidget()
    layout = QVBoxLayout(inner)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)

    scroll.setWidget(inner)
    outer_layout.addWidget(scroll)

    for name in _INTEGRATION_ORDER:
        module_name = f"integrations.{name}.settings_ui"
        try:
            mod = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        except Exception:
            logger.exception(f"Failed to load settings UI for {name}")
            continue

        builder = getattr(mod, "build_settings_sections", None)
        if builder is None:
            logger.warning(f"{module_name} has no build_settings_sections()")
            continue

        try:
            widgets = builder(pending, font, integration_manager=integration_manager)
            for w in widgets:
                layout.addWidget(w)
        except Exception:
            logger.exception(f"Failed to build settings for {name}")

    layout.addStretch()

    return page
