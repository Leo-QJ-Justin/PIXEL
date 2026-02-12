"""Tests for WeatherIntegration."""

import pytest


def _make_integration(tmp_path, settings=None):
    """Helper to create a WeatherIntegration instance."""
    from integrations.weather.integration import WeatherIntegration

    integration_path = tmp_path / "weather"
    integration_path.mkdir(exist_ok=True)
    return WeatherIntegration(integration_path, settings or {})


def _weather_response(condition_id, description="clear sky", temp=72, city="New York"):
    """Build a minimal OpenWeatherMap-style response dict."""
    return {
        "weather": [{"id": condition_id, "description": description}],
        "main": {"temp": temp},
        "name": city,
    }


@pytest.mark.unit
class TestWeatherIntegrationInit:
    """Tests for WeatherIntegration initialization."""

    def test_initialization(self, tmp_path):
        integration = _make_integration(tmp_path, {"enabled": True})
        assert integration._timer is None
        assert integration._last_weather_behavior is None
        assert integration._running is False
        assert integration.enabled is True

    def test_name(self, tmp_path):
        integration = _make_integration(tmp_path)
        assert integration.name == "weather"

    def test_display_name(self, tmp_path):
        integration = _make_integration(tmp_path)
        assert integration.display_name == "Weather Reactions"

    def test_default_settings(self, tmp_path):
        integration = _make_integration(tmp_path)
        defaults = integration.get_default_settings()
        assert defaults["enabled"] is True
        assert defaults["city"] == "New York"
        assert defaults["units"] == "imperial"
        assert defaults["check_interval_ms"] == 600000


@pytest.mark.unit
class TestConditionMapping:
    """Tests for _map_condition_to_behavior."""

    @pytest.mark.parametrize(
        "condition_id,expected",
        [
            (200, "rainy"),  # Thunderstorm
            (231, "rainy"),  # Thunderstorm with drizzle
            (300, "rainy"),  # Drizzle
            (500, "rainy"),  # Rain
            (502, "rainy"),  # Heavy rain
            (600, "rainy"),  # Snow
            (601, "rainy"),  # Heavy snow
            (800, "sunny"),  # Clear sky
            (801, None),  # Few clouds
            (802, None),  # Scattered clouds
            (741, None),  # Fog
        ],
    )
    def test_condition_mapping(self, condition_id, expected):
        from integrations.weather.integration import WeatherIntegration

        assert WeatherIntegration._map_condition_to_behavior(condition_id) == expected


@pytest.mark.unit
class TestProcessWeatherData:
    """Tests for _process_weather_data."""

    def test_rain_triggers_rainy(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "imperial"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        data = _weather_response(500, "light rain", 65, "Seattle")
        integration._process_weather_data(data)

        assert len(received) == 1
        assert received[0][0] == "rainy"
        assert received[0][1]["description"] == "Light rain"
        assert received[0][1]["temperature"] == "65\u00b0F"
        assert received[0][1]["city"] == "Seattle"

    def test_clear_triggers_sunny(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "imperial"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        data = _weather_response(800, "clear sky", 85, "Miami")
        integration._process_weather_data(data)

        assert len(received) == 1
        assert received[0][0] == "sunny"
        assert received[0][1]["description"] == "Clear sky"

    def test_clouds_trigger_nothing(self, tmp_path):
        integration = _make_integration(tmp_path)

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        data = _weather_response(802, "scattered clouds", 70)
        integration._process_weather_data(data)

        assert len(received) == 0

    def test_same_condition_does_not_retrigger(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "imperial"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        data = _weather_response(500, "light rain", 65)
        integration._process_weather_data(data)
        integration._process_weather_data(data)

        assert len(received) == 1

    def test_different_condition_triggers_again(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "imperial"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration._process_weather_data(_weather_response(500, "rain", 65))
        integration._process_weather_data(_weather_response(800, "clear sky", 80))

        assert len(received) == 2
        assert received[0][0] == "rainy"
        assert received[1][0] == "sunny"

    def test_metric_units_format(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "metric"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        data = _weather_response(800, "clear sky", 30, "Tokyo")
        integration._process_weather_data(data)

        assert received[0][1]["temperature"] == "30\u00b0C"

    def test_cleared_weather_resets_to_idle(self, tmp_path):
        """When weather goes from rain->clouds, pet returns to idle."""
        integration = _make_integration(tmp_path, {"units": "imperial"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration._process_weather_data(_weather_response(500, "rain", 65))
        integration._process_weather_data(_weather_response(802, "clouds", 68))

        assert len(received) == 2
        assert received[0][0] == "rainy"
        assert received[1][0] == "idle"

    def test_cleared_weather_allows_retrigger(self, tmp_path):
        """When weather goes from rain->clouds->rain, the second rain should trigger."""
        integration = _make_integration(tmp_path, {"units": "imperial"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration._process_weather_data(_weather_response(500, "rain", 65))
        integration._process_weather_data(_weather_response(802, "clouds", 68))
        integration._process_weather_data(_weather_response(501, "rain", 64))

        assert len(received) == 3
        assert received[0][0] == "rainy"
        assert received[1][0] == "idle"
        assert received[2][0] == "rainy"

    def test_empty_weather_list(self, tmp_path):
        integration = _make_integration(tmp_path)

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration._process_weather_data({"weather": [], "main": {}, "name": ""})

        assert len(received) == 0

    def test_missing_temperature(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "imperial"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        data = {"weather": [{"id": 800, "description": "clear sky"}], "main": {}, "name": "Test"}
        integration._process_weather_data(data)

        assert len(received) == 1
        assert received[0][1]["temperature"] == ""


@pytest.mark.unit
class TestStart:
    """Tests for start method."""

    @pytest.mark.asyncio
    async def test_start_without_api_key_logs_error(self, tmp_path, caplog, monkeypatch):
        monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)

        integration = _make_integration(tmp_path)
        await integration.start()

        assert "OPENWEATHER_API_KEY not configured" in caplog.text
        assert integration._timer is None
        assert integration._running is False


@pytest.mark.unit
class TestStop:
    """Tests for stop method."""

    @pytest.mark.asyncio
    async def test_stop_when_not_started(self, tmp_path):
        integration = _make_integration(tmp_path)
        await integration.stop()
        assert integration._timer is None
        assert integration._running is False
