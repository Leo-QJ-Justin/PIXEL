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

CLAY_RADIUS = "18px"
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
    "background": "#FEF3E2",
    "card": "#FFFFFF",
    "foreground": "#9A3412",
    "text": "#292524",
    "text_muted": "#57534E",
    "border": "#FDBA74",
    "border_strong": "#F97316",
    "border_subtle": "#FED7AA",
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
    "input_bg": "#FFFBF5",
}

# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------


def load_fonts() -> tuple[str, str]:
    """Load custom fonts and return (heading_family, body_family).

    Uses M PLUS Rounded 1c for a distinctive bubbly claymorphism feel.
    Falls back to Varela Round, then Nunito, then sans-serif.
    """
    fonts_dir = ASSETS_DIR / "fonts"

    # Primary: M PLUS Rounded 1c (bubbly, characterful)
    rounded = _load_font(fonts_dir / "MPLUSRounded1c-Medium.ttf")

    if rounded != "sans-serif":
        return rounded, rounded

    # Fallback chain
    heading = _load_font(fonts_dir / "VarelaRound-Regular.ttf")
    body = _load_font(fonts_dir / "NunitoSans-Regular.ttf")

    if heading == "sans-serif":
        heading = body
    if body == "sans-serif":
        body = heading

    return heading, body


def _load_font(path: Path) -> str:
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
            background-color: {c["background"]};
            font-family: '{font}';
        }}
        QLabel {{
            color: {c["text"]};
            font-family: '{font}';
            font-size: 14px;
        }}
        QLabel#section_title {{
            color: {c["foreground"]};
            font-family: '{font}';
            font-size: 15px;
            font-weight: bold;
        }}
        QLineEdit {{
            background-color: {c["input_bg"]};
            color: {c["text"]};
            border: 2px solid {c["border_subtle"]};
            border-radius: 10px;
            padding: 8px 12px;
            font-family: '{font}';
            font-size: 14px;
        }}
        QLineEdit:focus {{
            border: 2px solid {c["primary"]};
        }}
        QLineEdit:hover {{
            border: 2px solid {c["border"]};
        }}
        QTextEdit {{
            background-color: {c["input_bg"]};
            color: {c["text"]};
            border: 2px solid {c["border_subtle"]};
            border-radius: 10px;
            padding: 8px 12px;
            font-family: '{font}';
            font-size: 14px;
        }}
        QTextEdit:focus {{
            border: 2px solid {c["primary"]};
        }}
        QComboBox {{
            background-color: {c["input_bg"]};
            color: {c["text"]};
            border: 2px solid {c["border_subtle"]};
            border-radius: 10px;
            padding: 7px 12px;
            font-family: '{font}';
            font-size: 14px;
        }}
        QComboBox:hover {{
            border: 2px solid {c["border"]};
        }}
        QComboBox:focus {{
            border: 2px solid {c["primary"]};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 28px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c["card"]};
            color: {c["text"]};
            border: 2px solid {c["border"]};
            border-radius: 10px;
            selection-background-color: {c["muted"]};
            selection-color: {c["foreground"]};
            font-family: '{font}';
            font-size: 14px;
            padding: 4px;
        }}
        QCheckBox {{
            color: {c["text"]};
            font-family: '{font}';
            font-size: 14px;
            spacing: 10px;
        }}
        QCheckBox::indicator {{
            width: 22px;
            height: 22px;
            border: 2px solid {c["checkbox_border"]};
            border-radius: 7px;
            background-color: {c["input_bg"]};
        }}
        QCheckBox::indicator:checked {{
            background-color: {c["checkbox_checked"]};
            border: 2px solid {c["primary_pressed"]};
        }}
        QCheckBox::indicator:hover {{
            border: 2px solid {c["primary"]};
        }}
        QRadioButton {{
            color: {c["text"]};
            font-family: '{font}';
            font-size: 14px;
            spacing: 10px;
        }}
        QRadioButton::indicator {{
            width: 22px;
            height: 22px;
            border: 2px solid {c["checkbox_border"]};
            border-radius: 11px;
            background-color: {c["input_bg"]};
        }}
        QRadioButton::indicator:checked {{
            background-color: {c["checkbox_checked"]};
            border: 2px solid {c["primary_pressed"]};
        }}
        QRadioButton::indicator:hover {{
            border: 2px solid {c["primary"]};
        }}
        QTimeEdit, QDateEdit {{
            background-color: {c["input_bg"]};
            color: {c["text"]};
            border: 2px solid {c["border_subtle"]};
            border-radius: 10px;
            padding: 7px 10px;
            font-family: '{font}';
            font-size: 14px;
        }}
        QTimeEdit:focus, QDateEdit:focus {{
            border: 2px solid {c["primary"]};
        }}
        QSpinBox, QDoubleSpinBox {{
            background-color: {c["input_bg"]};
            color: {c["text"]};
            border: 2px solid {c["border_subtle"]};
            border-radius: 10px;
            padding: 7px 10px;
            font-family: '{font}';
            font-size: 14px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {c["primary"]};
        }}
        QSlider::groove:horizontal {{
            height: 8px;
            background-color: {c["slider_groove"]};
            border-radius: 4px;
        }}
        QSlider::sub-page:horizontal {{
            background-color: {c["slider_track"]};
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background-color: {c["slider_handle"]};
            border: 3px solid {c["primary_pressed"]};
            width: 20px;
            height: 20px;
            margin: -7px 0;
            border-radius: 11px;
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {c["primary_hover"]};
        }}
        QPushButton {{
            background-color: {c["muted"]};
            color: {c["foreground"]};
            border: 2px solid {c["border_subtle"]};
            border-radius: 12px;
            padding: 8px 16px;
            font-family: '{font}';
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: {c["border_subtle"]};
            border: 2px solid {c["border"]};
        }}
        QPushButton:pressed {{
            background-color: {c["border"]};
        }}
    """


def sidebar_style(font: str) -> str:
    """Return QSS for the sidebar navigation list."""
    c = COLORS
    return f"""
        QListWidget {{
            background-color: {c["sidebar_bg"]};
            color: {c["sidebar_text"]};
            border: none;
            font-family: '{font}';
            font-size: 14px;
            outline: none;
            padding-top: 8px;
        }}
        QListWidget::item {{
            padding: 14px 18px;
            border-radius: 10px;
            margin: 3px 8px;
            color: {c["sidebar_text"]};
            border-left: 4px solid transparent;
        }}
        QListWidget::item:hover {{
            background-color: {c["sidebar_hover"]};
            color: {c["sidebar_text_active"]};
        }}
        QListWidget::item:selected {{
            background-color: {c["sidebar_selected"]};
            color: {c["sidebar_text_active"]};
            border-left: 4px solid {c["primary"]};
            font-weight: bold;
        }}
    """


def header_style() -> str:
    """Return QSS for the dialog header bar."""
    c = COLORS
    return f"""
        QWidget#header {{
            background-color: {c["header_bg"]};
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
            background-color: {c["muted"]};
            border-top: 2px solid {c["border_subtle"]};
            border-bottom-left-radius: {CLAY_RADIUS};
            border-bottom-right-radius: {CLAY_RADIUS};
        }}
    """


def ok_button_style(font: str = "") -> str:
    """Return QSS for the OK / Save button."""
    c = COLORS
    font_rule = f"font-family: '{font}';" if font else ""
    return f"""
        QPushButton {{
            background-color: {c["ok_bg"]};
            color: #FFFFFF;
            border: {CLAY_BORDER} solid {c["primary_pressed"]};
            border-radius: 12px;
            padding: 8px 28px;
            font-size: 14px;
            font-weight: bold;
            {font_rule}
        }}
        QPushButton:hover {{
            background-color: {c["ok_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {c["ok_pressed"]};
        }}
    """


def cancel_button_style(font: str = "") -> str:
    """Return QSS for the Cancel button."""
    c = COLORS
    font_rule = f"font-family: '{font}';" if font else ""
    return f"""
        QPushButton {{
            background-color: {c["cancel_bg"]};
            color: #FFFFFF;
            border: {CLAY_BORDER} solid {c["cancel_pressed"]};
            border-radius: 12px;
            padding: 8px 28px;
            font-size: 14px;
            {font_rule}
        }}
        QPushButton:hover {{
            background-color: {c["cancel_hover"]};
            color: {c["text"]};
        }}
        QPushButton:pressed {{
            background-color: {c["cancel_pressed"]};
        }}
    """


def close_button_style() -> str:
    """Return QSS for the window close button in the header."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {c["sidebar_text"]};
            border: none;
            border-radius: 8px;
            padding: 4px 8px;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: {c["sidebar_hover"]};
            color: #FFFFFF;
        }}
        QPushButton:pressed {{
            background-color: {c["destructive"]};
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
            background-color: {c["scrollbar_bg"]};
            width: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background-color: {c["scrollbar_handle"]};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {c["border"]};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}
        QScrollBar:horizontal {{
            background-color: {c["scrollbar_bg"]};
            height: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {c["scrollbar_handle"]};
            border-radius: 4px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {c["border"]};
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
            background-color: {c["card"]};
            border: {CLAY_BORDER} solid {c["border_subtle"]};
            border-radius: {CLAY_RADIUS};
            padding: 14px;
        }}
        QGroupBox {{
            background-color: {c["card"]};
            border: {CLAY_BORDER} solid {c["border_subtle"]};
            border-radius: {CLAY_RADIUS};
            margin-top: 16px;
            padding: 14px 10px 10px 10px;
            font-size: 14px;
            font-weight: bold;
            color: {c["foreground"]};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {c["foreground"]};
            background-color: {c["card"]};
        }}
    """
