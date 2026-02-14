"""Tests for geocoding module and is_virtual_location."""

import pytest


@pytest.mark.unit
class TestIsVirtualLocation:
    """Tests for is_virtual_location."""

    @pytest.mark.parametrize(
        "location,expected",
        [
            ("https://zoom.us/j/123", True),
            ("https://meet.google.com/abc", True),
            ("https://teams.microsoft.com/l/meetup", True),
            ("123 Main St, Singapore", False),
            ("", False),
            ("Zoom Room 3", False),  # No zoom.us domain
        ],
    )
    def test_virtual_location_detection(self, location, expected):
        from integrations.google_calendar.calendar_event import is_virtual_location

        assert is_virtual_location(location) is expected

    def test_webex_is_virtual(self):
        from integrations.google_calendar.calendar_event import is_virtual_location

        assert is_virtual_location("https://webex.com/meet/abc") is True

    def test_discord_is_virtual(self):
        from integrations.google_calendar.calendar_event import is_virtual_location

        assert is_virtual_location("https://discord.gg/invite123") is True

    def test_http_url_is_virtual(self):
        from integrations.google_calendar.calendar_event import is_virtual_location

        assert is_virtual_location("http://example.com/meeting") is True

    def test_none_like_empty_is_not_virtual(self):
        from integrations.google_calendar.calendar_event import is_virtual_location

        assert is_virtual_location("") is False


@pytest.mark.unit
class TestGeocodeAddress:
    """Tests for geocode_address."""

    @pytest.mark.asyncio
    async def test_uses_google_when_key_set(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock, patch

        # Mock Google API key as present
        monkeypatch.setattr(
            "integrations.google_calendar.geocoding.GOOGLE_MAPS_API_KEY", "fake-key"
        )

        # Build mock aiohttp response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "results": [
                    {
                        "formatted_address": "123 Main St, Singapore 123456",
                        "geometry": {"location": {"lat": 1.3521, "lng": 103.8198}},
                    }
                ]
            }
        )

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=mock_resp)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        # Mock usage tracker
        mock_tracker = MagicMock()
        mock_tracker.can_call = MagicMock(return_value=True)
        mock_tracker.increment = MagicMock()

        with patch("integrations.google_calendar.geocoding.aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = mock_session

            from integrations.google_calendar.geocoding import geocode_address

            result = await geocode_address("123 Main St", mock_tracker)

        assert result is not None
        assert result.formatted_address == "123 Main St, Singapore 123456"
        assert result.lat == 1.3521
        assert result.lng == 103.8198
        mock_tracker.increment.assert_called_once_with("geocoding_api")

    @pytest.mark.asyncio
    async def test_falls_back_to_nominatim_when_no_google_key(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock, patch

        # No Google API key
        monkeypatch.setattr("integrations.google_calendar.geocoding.GOOGLE_MAPS_API_KEY", "")

        # Build mock Nominatim response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value=[
                {
                    "display_name": "123 Main Street, Singapore",
                    "lat": "1.3000",
                    "lon": "103.8000",
                }
            ]
        )
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=mock_resp)

        mock_tracker = MagicMock()
        mock_tracker.can_call = MagicMock(return_value=True)

        with patch("integrations.google_calendar.geocoding.aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = mock_session

            from integrations.google_calendar.geocoding import geocode_address

            # Patch asyncio.sleep to avoid the 1-second Nominatim rate limit delay
            with patch(
                "integrations.google_calendar.geocoding.asyncio.sleep", new_callable=AsyncMock
            ):
                result = await geocode_address("123 Main St", mock_tracker)

        assert result is not None
        assert result.formatted_address == "123 Main Street, Singapore"
        assert result.lat == 1.3
        assert result.lng == 103.8
        # Google increment should NOT have been called
        mock_tracker.increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_geocode_nominatim_with_mocked_response(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value=[
                {
                    "display_name": "Orchard Road, Singapore",
                    "lat": "1.3048",
                    "lon": "103.8318",
                }
            ]
        )
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch("integrations.google_calendar.geocoding.aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = mock_session

            from integrations.google_calendar.geocoding import _geocode_nominatim

            with patch(
                "integrations.google_calendar.geocoding.asyncio.sleep", new_callable=AsyncMock
            ):
                result = await _geocode_nominatim("Orchard Road")

        assert result is not None
        assert result.formatted_address == "Orchard Road, Singapore"
        assert result.lat == pytest.approx(1.3048)
        assert result.lng == pytest.approx(103.8318)

    @pytest.mark.asyncio
    async def test_geocode_nominatim_empty_response(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[])
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch("integrations.google_calendar.geocoding.aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = mock_session

            from integrations.google_calendar.geocoding import _geocode_nominatim

            with patch(
                "integrations.google_calendar.geocoding.asyncio.sleep", new_callable=AsyncMock
            ):
                result = await _geocode_nominatim("nonexistent place xyz")

        assert result is None
