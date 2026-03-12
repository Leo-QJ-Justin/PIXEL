"""Theme module for the Pomodoro timer widget.

Warm dark claymorphism palette that belongs to the same visual
family as the settings dialog (warm orange) but optimized for
focus sessions with a cozy dark background.
"""

from pathlib import Path

from PyQt6.QtGui import QFontDatabase

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"

CLAY_RADIUS = "16px"
CLAY_BORDER = "3px"
WIDGET_WIDTH = 280
RING_SIZE = 160
RING_THICKNESS = 8

COLORS: dict[str, str] = {
    "bg": "#1C1210",
    "surface": "#2A1F1A",
    "surface_light": "#3D2E25",
    "accent": "#F97316",
    "accent_glow": "#FB923C",
    "accent_dim": "#EA580C",
    "text": "#F5E6D3",
    "text_muted": "#A89484",
    "ring_focus": "#F97316",
    "ring_break": "#FBBF24",
    "success": "#A3D977",
    "success_dark": "#6B9B3A",
    "danger": "#F87171",
    "danger_dark": "#B91C1C",
    "diamond_filled": "#FBBF24",
    "diamond_empty": "#3D2E25",
    "border": "#4A3828",
    "input_bg": "#2A1F1A",
    "chart_bar": "#F97316",
    "chart_empty": "#3D2E25",
}


def load_font() -> str:
    """Load M PLUS Rounded 1c and return its family name. Falls back to 'sans-serif'."""
    fonts_dir = ASSETS_DIR / "fonts"
    path = fonts_dir / "MPLUSRounded1c-Medium.ttf"
    if path.exists():
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
    return "sans-serif"


def header_style(font: str) -> str:
    """Return QSS for the timer header bar."""
    c = COLORS
    return f"""
        QWidget#pomo_header {{
            background-color: {c['surface']};
            border-top-left-radius: {CLAY_RADIUS};
            border-top-right-radius: {CLAY_RADIUS};
            border: {CLAY_BORDER} solid {c['border']};
            border-bottom: none;
        }}
    """


def timer_page_style() -> str:
    """Return QSS for the main timer page background."""
    c = COLORS
    return f"""
        background: {c['bg']};
        border-bottom-left-radius: {CLAY_RADIUS};
        border-bottom-right-radius: {CLAY_RADIUS};
    """


def settings_page_style(font: str) -> str:
    """Return QSS for the settings page with slider/checkbox styling."""
    c = COLORS
    return f"""
        QWidget#pomo_settings_page {{
            background: {c['surface']};
            border-bottom-left-radius: {CLAY_RADIUS};
            border-bottom-right-radius: {CLAY_RADIUS};
        }}
        QLabel {{
            color: {c['text_muted']};
            font-family: '{font}';
            font-size: 10pt;
            background: transparent;
        }}
        QSlider::groove:horizontal {{
            border: 1px solid {c['border']};
            height: 8px;
            background: {c['surface_light']};
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background: {c['accent']};
            border: 2px solid {c['accent_dim']};
            width: 18px;
            margin: -6px 0;
            border-radius: 10px;
        }}
        QSlider::sub-page:horizontal {{
            background: {c['accent']};
            border-radius: 4px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {c['accent_glow']};
        }}
        QCheckBox {{
            color: {c['text_muted']};
            font-size: 10pt;
            spacing: 10px;
            background: transparent;
            font-family: '{font}';
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {c['border']};
            border-radius: 6px;
            background-color: {c['input_bg']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {c['accent']};
            border-color: {c['accent_dim']};
        }}
    """


def start_button_style(font: str) -> str:
    """Return QSS for START/PAUSE/BREAK buttons."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: {c['success']};
            border: {CLAY_BORDER} solid {c['success_dark']};
            border-radius: 12px;
            color: #1C1210;
            font-weight: bold;
            font-size: 10pt;
            font-family: '{font}';
            padding: 10px 22px;
        }}
        QPushButton:hover {{
            background-color: #B8E68B;
        }}
        QPushButton:pressed {{
            background-color: {c['success_dark']};
            color: #FFFFFF;
        }}
    """


def skip_button_style(font: str) -> str:
    """Return QSS for the SKIP button."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: {c['danger']};
            border: {CLAY_BORDER} solid {c['danger_dark']};
            border-radius: 12px;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 10pt;
            font-family: '{font}';
            padding: 10px 22px;
        }}
        QPushButton:hover {{
            background-color: #FCA5A5;
        }}
        QPushButton:pressed {{
            background-color: {c['danger_dark']};
        }}
    """


def link_button_style() -> str:
    """Return QSS for text link buttons."""
    c = COLORS
    return f"""
        QPushButton {{
            background: transparent;
            border: none;
            color: {c['text_muted']};
            font-size: 9pt;
            text-decoration: underline;
        }}
        QPushButton:hover {{
            color: {c['text']};
        }}
    """


def icon_button_style() -> str:
    """Return QSS for icon buttons."""
    c = COLORS
    return f"""
        QPushButton {{
            background: transparent;
            border: none;
            color: {c['text_muted']};
            font-size: 14pt;
        }}
        QPushButton:hover {{
            color: {c['accent']};
        }}
    """


def close_button_style() -> str:
    """Return QSS for close X button."""
    c = COLORS
    return f"""
        QPushButton {{
            background: transparent;
            border: none;
            color: {c['text_muted']};
            font-size: 14pt;
            font-weight: bold;
        }}
        QPushButton:hover {{
            color: {c['danger']};
        }}
    """


def ok_button_style(font: str) -> str:
    """Return QSS for the OK button in settings."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: {c['success']};
            border: {CLAY_BORDER} solid {c['success_dark']};
            border-radius: 10px;
            color: #1C1210;
            font-weight: bold;
            font-size: 10pt;
            font-family: '{font}';
            padding: 8px 18px;
        }}
        QPushButton:hover {{
            background-color: #B8E68B;
        }}
    """


def cancel_button_style(font: str) -> str:
    """Return QSS for the Cancel button in settings."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: {c['surface_light']};
            border: {CLAY_BORDER} solid {c['border']};
            border-radius: 10px;
            color: {c['text_muted']};
            font-weight: bold;
            font-size: 10pt;
            font-family: '{font}';
            padding: 8px 18px;
        }}
        QPushButton:hover {{
            background-color: {c['border']};
            color: {c['text']};
        }}
    """


def back_button_style(font: str) -> str:
    """Return QSS for the Back button in stats view."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: {c['surface_light']};
            border: {CLAY_BORDER} solid {c['border']};
            border-radius: 10px;
            color: {c['text_muted']};
            font-weight: bold;
            font-size: 10pt;
            font-family: '{font}';
            padding: 8px 18px;
        }}
        QPushButton:hover {{
            background-color: {c['border']};
            color: {c['text']};
        }}
    """
