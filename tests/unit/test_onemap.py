"""Tests for OneMap Singapore routing client."""

import pytest


@pytest.mark.unit
class TestParseOnemapResponse:
    """Tests for _parse_onemap_response."""

    def test_drive_response(self):
        from integrations.google_calendar.onemap import _parse_onemap_response

        data = {"route_summary": {"total_time": 1800}}
        result = _parse_onemap_response(data, "DRIVE")

        assert result is not None
        assert result.mode == "DRIVE"
        assert result.duration_minutes == pytest.approx(30.0)

    def test_pt_response(self):
        from integrations.google_calendar.onemap import _parse_onemap_response

        data = {"plan": {"itineraries": [{"duration": 2400}]}}
        result = _parse_onemap_response(data, "TRANSIT")

        assert result is not None
        assert result.mode == "TRANSIT"
        assert result.duration_minutes == pytest.approx(40.0)

    def test_empty_data_returns_none(self):
        from integrations.google_calendar.onemap import _parse_onemap_response

        data = {}
        result = _parse_onemap_response(data, "DRIVE")

        assert result is None

    def test_empty_route_summary_returns_none(self):
        from integrations.google_calendar.onemap import _parse_onemap_response

        data = {"route_summary": {"total_time": 0}}
        result = _parse_onemap_response(data, "WALK")

        assert result is None

    def test_empty_itineraries_returns_none(self):
        from integrations.google_calendar.onemap import _parse_onemap_response

        data = {"plan": {"itineraries": []}}
        result = _parse_onemap_response(data, "TRANSIT")

        assert result is None

    def test_walk_mode(self):
        from integrations.google_calendar.onemap import _parse_onemap_response

        data = {"route_summary": {"total_time": 900}}
        result = _parse_onemap_response(data, "WALK")

        assert result is not None
        assert result.mode == "WALK"
        assert result.duration_minutes == pytest.approx(15.0)

    def test_bicycle_mode(self):
        from integrations.google_calendar.onemap import _parse_onemap_response

        data = {"route_summary": {"total_time": 600}}
        result = _parse_onemap_response(data, "BICYCLE")

        assert result is not None
        assert result.mode == "BICYCLE"
        assert result.duration_minutes == pytest.approx(10.0)


@pytest.mark.unit
class TestModeMapping:
    """Tests for mode mapping from Google mode names to OneMap routeType."""

    @pytest.mark.parametrize(
        "google_mode,onemap_mode",
        [
            ("DRIVE", "drive"),
            ("TRANSIT", "pt"),
            ("WALK", "walk"),
            ("BICYCLE", "cycle"),
        ],
    )
    def test_mode_map(self, google_mode, onemap_mode):
        from integrations.google_calendar.onemap import _MODE_MAP

        assert _MODE_MAP[google_mode] == onemap_mode

    def test_unsupported_mode_not_in_map(self):
        from integrations.google_calendar.onemap import _MODE_MAP

        assert "FLY" not in _MODE_MAP
