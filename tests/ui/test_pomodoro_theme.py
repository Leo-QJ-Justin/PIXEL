"""Tests for src.ui.pomodoro_theme."""

import re

import pytest

from src.ui import pomodoro_theme as theme

# ── Color tokens ──────────────────────────────────────────────────────

REQUIRED_TOKENS = [
    "bg",
    "surface",
    "surface_light",
    "accent",
    "accent_glow",
    "accent_dim",
    "text",
    "text_muted",
    "ring_focus",
    "ring_break",
    "success",
    "success_dark",
    "danger",
    "danger_dark",
    "diamond_filled",
    "diamond_empty",
    "border",
    "input_bg",
    "chart_bar",
    "chart_empty",
]

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class TestColors:
    def test_colors_dict_exists(self):
        assert isinstance(theme.COLORS, dict)

    @pytest.mark.parametrize("token", REQUIRED_TOKENS)
    def test_has_required_token(self, token: str):
        assert token in theme.COLORS

    @pytest.mark.parametrize("token", REQUIRED_TOKENS)
    def test_values_are_hex(self, token: str):
        assert HEX_RE.match(theme.COLORS[token]), f"{token} = {theme.COLORS[token]}"


# ── Constants ─────────────────────────────────────────────────────────


class TestConstants:
    def test_clay_radius(self):
        assert theme.CLAY_RADIUS == "16px"

    def test_clay_border(self):
        assert theme.CLAY_BORDER == "3px"

    def test_widget_width(self):
        assert theme.WIDGET_WIDTH == 280

    def test_ring_size(self):
        assert theme.RING_SIZE == 160

    def test_ring_thickness(self):
        assert theme.RING_THICKNESS == 8


# ── QSS generators ───────────────────────────────────────────────────

FONT = "TestFont"


class TestQSSGenerators:
    def test_header_style(self):
        qss = theme.header_style(FONT)
        assert "background" in qss
        assert "pomo_header" in qss

    def test_timer_page_style(self):
        qss = theme.timer_page_style()
        assert "background" in qss
        assert "border-bottom-left-radius" in qss

    def test_settings_page_style(self):
        qss = theme.settings_page_style(FONT)
        assert "QSlider" in qss
        assert "QCheckBox" in qss
        assert FONT in qss

    def test_start_button_style(self):
        qss = theme.start_button_style(FONT)
        assert "QPushButton" in qss
        assert FONT in qss

    def test_skip_button_style(self):
        qss = theme.skip_button_style(FONT)
        assert "QPushButton" in qss
        assert FONT in qss

    def test_link_button_style(self):
        qss = theme.link_button_style()
        assert "QPushButton" in qss
        assert "underline" in qss

    def test_icon_button_style(self):
        qss = theme.icon_button_style()
        assert "QPushButton" in qss

    def test_close_button_style(self):
        qss = theme.close_button_style()
        assert "QPushButton" in qss

    def test_ok_button_style(self):
        qss = theme.ok_button_style(FONT)
        assert "QPushButton" in qss
        assert FONT in qss

    def test_cancel_button_style(self):
        qss = theme.cancel_button_style(FONT)
        assert "QPushButton" in qss
        assert FONT in qss

    def test_back_button_style(self):
        qss = theme.back_button_style(FONT)
        assert "QPushButton" in qss
        assert FONT in qss
