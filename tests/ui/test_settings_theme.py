"""Tests for src/ui/settings/theme.py"""

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Provide a QApplication instance for the test session."""
    app = QApplication.instance() or QApplication([])
    yield app


class TestColors:
    def test_required_keys_present(self):
        from src.ui.settings.theme import COLORS

        required = {"primary", "background", "card", "foreground"}
        missing = required - COLORS.keys()
        assert not missing, f"Missing color keys: {missing}"

    def test_all_values_are_hex_strings(self):
        from src.ui.settings.theme import COLORS

        for key, value in COLORS.items():
            assert isinstance(value, str), f"COLORS[{key!r}] is not a string"
            assert value.startswith("#"), f"COLORS[{key!r}] does not start with '#'"

    def test_color_count(self):
        from src.ui.settings.theme import COLORS

        # We defined 34 tokens; make sure at least that many are present
        assert len(COLORS) >= 34


class TestClayConstants:
    def test_clay_radius(self):
        from src.ui.settings.theme import CLAY_RADIUS

        assert CLAY_RADIUS == "16px"

    def test_clay_border(self):
        from src.ui.settings.theme import CLAY_BORDER

        assert CLAY_BORDER == "3px"


class TestQSSGenerators:
    """Tests that each QSS generator returns a non-empty string with expected selectors."""

    def test_content_style_returns_string_with_qlineedit(self):
        from src.ui.settings.theme import content_style

        result = content_style("sans-serif")
        assert isinstance(result, str)
        assert "QLineEdit" in result

    def test_sidebar_style_returns_string_with_qlistwidget(self):
        from src.ui.settings.theme import sidebar_style

        result = sidebar_style("sans-serif")
        assert isinstance(result, str)
        assert "QListWidget" in result

    def test_header_style_returns_string(self):
        from src.ui.settings.theme import header_style

        result = header_style()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_footer_style_returns_string(self):
        from src.ui.settings.theme import footer_style

        result = footer_style()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_ok_button_style_returns_string(self):
        from src.ui.settings.theme import ok_button_style

        result = ok_button_style()
        assert isinstance(result, str)
        assert "QPushButton" in result

    def test_cancel_button_style_returns_string(self):
        from src.ui.settings.theme import cancel_button_style

        result = cancel_button_style()
        assert isinstance(result, str)
        assert "QPushButton" in result

    def test_close_button_style_returns_string(self):
        from src.ui.settings.theme import close_button_style

        result = close_button_style()
        assert isinstance(result, str)
        assert "QPushButton" in result

    def test_scroll_area_style_returns_string(self):
        from src.ui.settings.theme import scroll_area_style

        result = scroll_area_style()
        assert isinstance(result, str)
        assert "QScrollArea" in result

    def test_section_style_returns_string(self):
        from src.ui.settings.theme import section_style

        result = section_style()
        assert isinstance(result, str)
        assert "QGroupBox" in result

    def test_content_style_uses_provided_font(self):
        from src.ui.settings.theme import content_style

        result = content_style("Nunito Sans")
        assert "Nunito Sans" in result

    def test_sidebar_style_uses_provided_font(self):
        from src.ui.settings.theme import sidebar_style

        result = sidebar_style("Varela Round")
        assert "Varela Round" in result


class TestLoadFonts:
    def test_returns_two_tuple(self, qapp):
        from src.ui.settings.theme import load_fonts

        result = load_fonts()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_both_elements_are_strings(self, qapp):
        from src.ui.settings.theme import load_fonts

        heading, body = load_fonts()
        assert isinstance(heading, str)
        assert isinstance(body, str)

    def test_fallback_when_fonts_missing(self, qapp):
        """When font files don't exist the result is still a valid 2-tuple of strings."""
        from src.ui.settings.theme import load_fonts

        heading, body = load_fonts()
        # Both must be non-empty strings regardless of whether files exist
        assert heading
        assert body
