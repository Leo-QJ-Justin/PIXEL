"""Tests for Google Routes API client."""

import pytest


@pytest.mark.unit
class TestParseRouteResponse:
    """Tests for _parse_route_response."""

    def test_valid_response(self):
        from integrations.google_calendar.routes import _parse_route_response

        data = {"routes": [{"duration": "1234s"}]}
        result = _parse_route_response(data, "DRIVE")

        assert result is not None
        assert result.mode == "DRIVE"
        assert result.duration_minutes == pytest.approx(1234 / 60)

    def test_empty_routes(self):
        from integrations.google_calendar.routes import _parse_route_response

        data = {"routes": []}
        result = _parse_route_response(data, "DRIVE")

        assert result is None

    def test_missing_routes_key(self):
        from integrations.google_calendar.routes import _parse_route_response

        data = {}
        result = _parse_route_response(data, "DRIVE")

        assert result is None

    def test_missing_duration(self):
        from integrations.google_calendar.routes import _parse_route_response

        data = {"routes": [{}]}
        result = _parse_route_response(data, "TRANSIT")

        assert result is None

    def test_empty_duration_string(self):
        from integrations.google_calendar.routes import _parse_route_response

        data = {"routes": [{"duration": ""}]}
        result = _parse_route_response(data, "WALK")

        assert result is None

    def test_transit_mode_preserved(self):
        from integrations.google_calendar.routes import _parse_route_response

        data = {"routes": [{"duration": "600s"}]}
        result = _parse_route_response(data, "TRANSIT")

        assert result is not None
        assert result.mode == "TRANSIT"
        assert result.duration_minutes == pytest.approx(10.0)


@pytest.mark.unit
class TestComputeTravelTime:
    """Tests for compute_travel_time."""

    @pytest.mark.asyncio
    async def test_skips_modes_when_quota_exhausted(self, monkeypatch):
        from unittest.mock import MagicMock

        monkeypatch.setattr("integrations.google_calendar.routes.GOOGLE_MAPS_API_KEY", "fake-key")

        mock_tracker = MagicMock()
        # Quota exhausted — can_call always returns False
        mock_tracker.can_call = MagicMock(return_value=False)

        from integrations.google_calendar.routes import compute_travel_time

        result = await compute_travel_time(
            "Origin", "Destination", ["DRIVE", "TRANSIT"], mock_tracker
        )

        # Should return None since no modes could be queried
        assert result is None
        # _query_route should never be called
        mock_tracker.increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_without_api_key(self, monkeypatch):
        from unittest.mock import MagicMock

        monkeypatch.setattr("integrations.google_calendar.routes.GOOGLE_MAPS_API_KEY", "")

        mock_tracker = MagicMock()

        from integrations.google_calendar.routes import compute_travel_time

        result = await compute_travel_time("Origin", "Destination", ["DRIVE"], mock_tracker)

        assert result is None

    @pytest.mark.asyncio
    async def test_queries_multiple_modes(self, monkeypatch):
        from unittest.mock import MagicMock, patch

        from integrations.google_calendar.calendar_event import TravelEstimate

        monkeypatch.setattr("integrations.google_calendar.routes.GOOGLE_MAPS_API_KEY", "fake-key")

        mock_tracker = MagicMock()
        mock_tracker.can_call = MagicMock(return_value=True)

        drive_estimate = TravelEstimate(mode="DRIVE", duration_minutes=20.0)
        transit_estimate = TravelEstimate(mode="TRANSIT", duration_minutes=35.0)
        call_count = 0

        async def mock_query_route(origin, destination, mode):
            nonlocal call_count
            call_count += 1
            if mode == "DRIVE":
                return drive_estimate
            return transit_estimate

        with patch(
            "integrations.google_calendar.routes._query_route",
            side_effect=mock_query_route,
        ):
            from integrations.google_calendar.routes import compute_travel_time

            result = await compute_travel_time("Home", "Office", ["DRIVE", "TRANSIT"], mock_tracker)

        assert result is not None
        assert len(result) == 2
        assert result[0].mode == "DRIVE"
        assert result[0].duration_minutes == 20.0
        assert result[1].mode == "TRANSIT"
        assert result[1].duration_minutes == 35.0
        assert mock_tracker.increment.call_count == 2


@pytest.mark.unit
class TestQueryRoute:
    """Tests for _query_route with mocked aiohttp."""

    @pytest.mark.asyncio
    async def test_successful_query(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock, patch

        monkeypatch.setattr("integrations.google_calendar.routes.GOOGLE_MAPS_API_KEY", "fake-key")

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"routes": [{"duration": "1800s"}]})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=mock_resp)

        with patch("integrations.google_calendar.routes.aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = mock_session

            from integrations.google_calendar.routes import _query_route

            result = await _query_route("Home", "Office", "DRIVE")

        assert result is not None
        assert result.mode == "DRIVE"
        assert result.duration_minutes == pytest.approx(30.0)

    @pytest.mark.asyncio
    async def test_api_error_returns_none(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock, patch

        monkeypatch.setattr("integrations.google_calendar.routes.GOOGLE_MAPS_API_KEY", "fake-key")

        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.text = AsyncMock(return_value="Internal Server Error")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=mock_resp)

        with patch("integrations.google_calendar.routes.aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = mock_session

            from integrations.google_calendar.routes import _query_route

            result = await _query_route("Home", "Office", "DRIVE")

        assert result is None
