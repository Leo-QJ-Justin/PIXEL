"""Theme module for the settings dialog.

Provides color tokens, font loading, and QSS style generators
using a warm claymorphism design language.
"""

from pathlib import Path

from PyQt6.QtGui import QFontDatabase

# ---------------------------------------------------------------------------
# Asset paths
# ---------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "assets"

# ---------------------------------------------------------------------------
# Claymorphism constants
# ---------------------------------------------------------------------------

CLAY_RADIUS = "16px"
CLAY_BORDER = "3px"

# ---------------------------------------------------------------------------
# Color palette – Pet Tech App (warm orange / cream / blue)
# ---------------------------------------------------------------------------

COLORS: dict[str, str] = {
    "primary": "#F97316",
    "primary_hover": "#FB923C",
    "primary_pressed": "#EA580C",
    "accent": "#2563EB",
    "accent_light": "#3B82F6",
    "background": "#FFF7ED",
    "card": "#FFFFFF",
    "foreground": "#9A3412",
    "text": "#44403C",
    "text_muted": "#57534E",
    "border": "#FED7AA",
    "border_strong": "#FDBA74",
    "muted": "#FFF1E6",
    "sidebar_bg": "#7C2D12",
    "sidebar_selected": "#9A3412",
    "sidebar_hover": "#6C2710",
    "sidebar_text": "#FED7AA",
    "sidebar_text_active": "#FFFFFF",
    "header_bg": "#7C2D12",
    "ok_bg": "#F97316",
    "ok_hover": "#FB923C",
    "ok_pressed": "#EA580C",
    "cancel_bg": "#A8A29E",
    "cancel_hover": "#D6D3D1",
    "cancel_pressed": "#78716C",
    "destructive": "#DC2626",
    "success": "#16A34A",
    "checkbox_checked": "#F97316",
    "checkbox_border": "#D6D3D1",
    "slider_handle": "#F97316",
    "slider_track": "#FDBA74",
    "slider_groove": "#E7E5E4",
    "scrollbar_bg": "#FFF1E6",
    "scrollbar_handle": "#D6D3D1",
}

# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------


def load_fonts() -> tuple[str, str]:
    """Load custom fonts and return (heading_family, body_family).

    Tries Varela Round for headings and Nunito Sans for body text.
    Falls back to M+ Rounded 1c, then "sans-serif".
    """
    fonts_dir = ASSETS_DIR / "fonts"

    heading_family = _load_font(fonts_dir / "VarelaRound-Regular.ttf", "Varela Round")
    body_family = _load_font(fonts_dir / "NunitoSans-Regular.ttf", "Nunito Sans")

    # Apply M+ Rounded 1c fallback for whichever failed
    fallback_family = _load_font(fonts_dir / "MPLUSRounded1c-Regular.ttf", "M PLUS Rounded 1c")
    final_fallback = fallback_family if fallback_family != "sans-serif" else "sans-serif"

    if heading_family == "sans-serif":
        heading_family = final_fallback
    if body_family == "sans-serif":
        body_family = final_fallback

    return heading_family, body_family


def _load_font(path: Path, preferred_family: str) -> str:
    """Attempt to load a font file; return its family name or 'sans-serif'."""
    if path.exists():
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
    return "sans-serif"


# ---------------------------------------------------------------------------
# QSS style generators
# ---------------------------------------------------------------------------


def content_style(font: str) -> str:
    """Return QSS for the main content area."""
    c = COLORS
    return f"""
        QWidget#content_area {{
            background-color: {c['background']};
            font-family: '{font}';
        }}
        QLabel {{
            color: {c['text']};
            font-family: '{font}';
            font-size: 13px;
        }}
        QLabel#section_title {{
            color: {c['foreground']};
            font-family: '{font}';
            font-size: 14px;
            font-weight: bold;
        }}
        QLineEdit {{
            background-color: {c['card']};
            color: {c['text']};
            border: 2px solid {c['border']};
            border-radius: 8px;
            padding: 6px 10px;
            font-family: '{font}';
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 2px solid {c['primary']};
        }}
        QLineEdit:hover {{
            border: 2px solid {c['border_strong']};
        }}
        QTextEdit {{
            background-color: {c['card']};
            color: {c['text']};
            border: 2px solid {c['border']};
            border-radius: 8px;
            padding: 6px 10px;
            font-family: '{font}';
            font-size: 13px;
        }}
        QTextEdit:focus {{
            border: 2px solid {c['primary']};
        }}
        QComboBox {{
            background-color: {c['card']};
            color: {c['text']};
            border: 2px solid {c['border']};
            border-radius: 8px;
            padding: 5px 10px;
            font-family: '{font}';
            font-size: 13px;
        }}
        QComboBox:hover {{
            border: 2px solid {c['border_strong']};
        }}
        QComboBox:focus {{
            border: 2px solid {c['primary']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c['card']};
            color: {c['text']};
            border: 2px solid {c['border']};
            border-radius: 8px;
            selection-background-color: {c['muted']};
            selection-color: {c['foreground']};
        }}
        QCheckBox {{
            color: {c['text']};
            font-family: '{font}';
            font-size: 13px;
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {c['checkbox_border']};
            border-radius: 6px;
            background-color: {c['card']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {c['checkbox_checked']};
            border: 2px solid {c['primary_pressed']};
        }}
        QCheckBox::indicator:hover {{
            border: 2px solid {c['primary']};
        }}
        QSpinBox, QDoubleSpinBox {{
            background-color: {c['card']};
            color: {c['text']};
            border: 2px solid {c['border']};
            border-radius: 8px;
            padding: 5px 8px;
            font-family: '{font}';
            font-size: 13px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {c['primary']};
        }}
        QSlider::groove:horizontal {{
            height: 6px;
            background-color: {c['slider_groove']};
            border-radius: 3px;
        }}
        QSlider::sub-page:horizontal {{
            background-color: {c['slider_track']};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background-color: {c['slider_handle']};
            border: 2px solid {c['primary_pressed']};
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {c['primary_hover']};
        }}
        QPushButton {{
            background-color: {c['muted']};
            color: {c['foreground']};
            border: 2px solid {c['border']};
            border-radius: 10px;
            padding: 6px 14px;
            font-family: '{font}';
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {c['border']};
        }}
        QPushButton:pressed {{
            background-color: {c['border_strong']};
        }}
    """


def sidebar_style(font: str) -> str:
    """Return QSS for the sidebar navigation list."""
    c = COLORS
    return f"""
        QListWidget {{
            background-color: {c['sidebar_bg']};
            color: {c['sidebar_text']};
            border: none;
            font-family: '{font}';
            font-size: 13px;
            outline: none;
        }}
        QListWidget::item {{
            padding: 12px 16px;
            border-radius: 8px;
            margin: 2px 6px;
            color: {c['sidebar_text']};
            border-left: 4px solid transparent;
        }}
        QListWidget::item:hover {{
            background-color: {c['sidebar_hover']};
            color: {c['sidebar_text_active']};
        }}
        QListWidget::item:selected {{
            background-color: {c['sidebar_selected']};
            color: {c['sidebar_text_active']};
            border-left: 4px solid {c['primary']};
        }}
    """


def header_style() -> str:
    """Return QSS for the dialog header bar."""
    c = COLORS
    return f"""
        QWidget#header {{
            background-color: {c['header_bg']};
            border-top-left-radius: {CLAY_RADIUS};
            border-top-right-radius: {CLAY_RADIUS};
        }}
        QLabel#header_title {{
            color: #FFFFFF;
            font-size: 16px;
            font-weight: bold;
        }}
    """


def footer_style() -> str:
    """Return QSS for the dialog footer bar."""
    c = COLORS
    return f"""
        QWidget#footer {{
            background-color: {c['muted']};
            border-top: 2px solid {c['border']};
            border-bottom-left-radius: {CLAY_RADIUS};
            border-bottom-right-radius: {CLAY_RADIUS};
        }}
    """


def ok_button_style() -> str:
    """Return QSS for the OK / Save button."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: {c['ok_bg']};
            color: #FFFFFF;
            border: {CLAY_BORDER} solid {c['primary_pressed']};
            border-radius: 10px;
            padding: 7px 22px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {c['ok_hover']};
        }}
        QPushButton:pressed {{
            background-color: {c['ok_pressed']};
        }}
    """


def cancel_button_style() -> str:
    """Return QSS for the Cancel button."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: {c['cancel_bg']};
            color: #FFFFFF;
            border: {CLAY_BORDER} solid {c['cancel_pressed']};
            border-radius: 10px;
            padding: 7px 22px;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {c['cancel_hover']};
            color: {c['text']};
        }}
        QPushButton:pressed {{
            background-color: {c['cancel_pressed']};
        }}
    """


def close_button_style() -> str:
    """Return QSS for the window close button in the header."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {c['sidebar_text']};
            border: none;
            border-radius: 8px;
            padding: 4px 8px;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: {c['sidebar_hover']};
            color: #FFFFFF;
        }}
        QPushButton:pressed {{
            background-color: {c['destructive']};
            color: #FFFFFF;
        }}
    """


def scroll_area_style() -> str:
    """Return QSS for scroll areas and their scrollbars."""
    c = COLORS
    return f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            background-color: {c['scrollbar_bg']};
            width: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background-color: {c['scrollbar_handle']};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {c['border_strong']};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}
        QScrollBar:horizontal {{
            background-color: {c['scrollbar_bg']};
            height: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {c['scrollbar_handle']};
            border-radius: 4px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {c['border_strong']};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0;
            background: none;
        }}
    """


def section_style() -> str:
    """Return QSS for card/section containers."""
    c = COLORS
    return f"""
        QFrame#section_card {{
            background-color: {c['card']};
            border: {CLAY_BORDER} solid {c['border']};
            border-radius: {CLAY_RADIUS};
            padding: 12px;
        }}
        QGroupBox {{
            background-color: {c['card']};
            border: {CLAY_BORDER} solid {c['border']};
            border-radius: {CLAY_RADIUS};
            margin-top: 16px;
            padding: 12px 8px 8px 8px;
            font-size: 13px;
            font-weight: bold;
            color: {c['foreground']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {c['foreground']};
            background-color: {c['card']};
        }}
    """
