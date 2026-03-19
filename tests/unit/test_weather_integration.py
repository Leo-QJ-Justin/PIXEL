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
        assert defaults["units"] == "metric"
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
            (800, None),  # Clear sky — bubble only
            (801, None),  # Few clouds — bubble only
            (802, None),  # Scattered clouds — bubble only
            (741, None),  # Fog — bubble only
        ],
    )
    def test_condition_mapping(self, condition_id, expected):
        from integrations.weather.integration import WeatherIntegration

        assert WeatherIntegration._map_condition_to_behavior(condition_id) == expected


@pytest.mark.unit
class TestProcessWeatherData:
    """Tests for _process_weather_data."""

    def test_rain_triggers_rainy_behavior(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "imperial"})

        behaviors = []
        integration.request_behavior.connect(lambda name, ctx: behaviors.append((name, ctx)))

        data = _weather_response(500, "light rain", 65, "Seattle")
        integration._process_weather_data(data)

        assert len(behaviors) == 1
        assert behaviors[0][0] == "rainy"
        assert behaviors[0][1]["description"] == "Light rain"
        assert behaviors[0][1]["temperature"] == "65\u00b0F"
        assert behaviors[0][1]["city"] == "Seattle"
        assert "bubble_text" in behaviors[0][1]

    def test_clear_sends_notification(self, tmp_path):
        """Clear sky sends a bubble notification, not a behavior trigger."""
        integration = _make_integration(tmp_path, {"units": "imperial"})

        behaviors = []
        notifications = []
        integration.request_behavior.connect(lambda name, ctx: behaviors.append((name, ctx)))
        integration.request_notification.connect(lambda ctx: notifications.append(ctx))

        data = _weather_response(800, "clear sky", 85, "Miami")
        integration._process_weather_data(data)

        assert len(behaviors) == 0
        assert len(notifications) == 1
        assert notifications[0]["description"] == "Clear sky"
        assert "bubble_text" in notifications[0]

    def test_clouds_send_notification_on_first_check(self, tmp_path):
        """Clouds on first check send a bubble notification."""
        integration = _make_integration(tmp_path)

        notifications = []
        integration.request_notification.connect(lambda ctx: notifications.append(ctx))

        data = _weather_response(802, "scattered clouds", 70)
        integration._process_weather_data(data)

        assert len(notifications) == 1

    def test_same_condition_does_not_retrigger(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "imperial"})

        behaviors = []
        integration.request_behavior.connect(lambda name, ctx: behaviors.append((name, ctx)))

        data = _weather_response(500, "light rain", 65)
        integration._process_weather_data(data)
        integration._process_weather_data(data)

        assert len(behaviors) == 1

    def test_same_non_precipitation_does_not_retrigger(self, tmp_path):
        """Same non-precipitation condition repeated doesn't send another notification."""
        integration = _make_integration(tmp_path)

        notifications = []
        integration.request_notification.connect(lambda ctx: notifications.append(ctx))

        data = _weather_response(800, "clear sky", 85)
        integration._process_weather_data(data)
        integration._process_weather_data(data)

        assert len(notifications) == 1

    def test_rain_to_clear_triggers_notification(self, tmp_path):
        """When weather clears from rain, a notification is sent (not a behavior)."""
        integration = _make_integration(tmp_path, {"units": "imperial"})

        behaviors = []
        notifications = []
        integration.request_behavior.connect(lambda name, ctx: behaviors.append((name, ctx)))
        integration.request_notification.connect(lambda ctx: notifications.append(ctx))

        integration._process_weather_data(_weather_response(500, "rain", 65))
        integration._process_weather_data(_weather_response(802, "clouds", 68))

        assert len(behaviors) == 1
        assert behaviors[0][0] == "rainy"
        assert len(notifications) == 1
        assert notifications[0]["description"] == "Clouds"

    def test_rain_clear_rain_retriggers(self, tmp_path):
        """rain -> clear -> rain should trigger rainy twice."""
        integration = _make_integration(tmp_path, {"units": "imperial"})

        behaviors = []
        notifications = []
        integration.request_behavior.connect(lambda name, ctx: behaviors.append((name, ctx)))
        integration.request_notification.connect(lambda ctx: notifications.append(ctx))

        integration._process_weather_data(_weather_response(500, "rain", 65))
        integration._process_weather_data(_weather_response(802, "clouds", 68))
        integration._process_weather_data(_weather_response(501, "rain", 64))

        assert len(behaviors) == 2
        assert behaviors[0][0] == "rainy"
        assert behaviors[1][0] == "rainy"
        assert len(notifications) == 1  # clouds notification

    def test_metric_units_format(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "metric"})

        notifications = []
        integration.request_notification.connect(lambda ctx: notifications.append(ctx))

        data = _weather_response(800, "clear sky", 30, "Tokyo")
        integration._process_weather_data(data)

        assert len(notifications) == 1
        assert notifications[0]["temperature"] == "30\u00b0C"

    def test_bubble_text_format(self, tmp_path):
        """Bubble text should include description, temperature, and city."""
        integration = _make_integration(tmp_path, {"units": "metric"})

        behaviors = []
        integration.request_behavior.connect(lambda name, ctx: behaviors.append((name, ctx)))

        data = _weather_response(500, "light rain", 25, "Singapore")
        integration._process_weather_data(data)

        assert len(behaviors) == 1
        bubble = behaviors[0][1]["bubble_text"]
        assert "Light rain" in bubble
        assert "25\u00b0C" in bubble
        assert "Singapore" in bubble

    def test_empty_weather_list(self, tmp_path):
        integration = _make_integration(tmp_path)

        behaviors = []
        notifications = []
        integration.request_behavior.connect(lambda name, ctx: behaviors.append((name, ctx)))
        integration.request_notification.connect(lambda ctx: notifications.append(ctx))

        integration._process_weather_data({"weather": [], "main": {}, "name": ""})

        assert len(behaviors) == 0
        assert len(notifications) == 0

    def test_missing_temperature(self, tmp_path):
        integration = _make_integration(tmp_path, {"units": "imperial"})

        notifications = []
        integration.request_notification.connect(lambda ctx: notifications.append(ctx))

        data = {"weather": [{"id": 800, "description": "clear sky"}], "main": {}, "name": "Test"}
        integration._process_weather_data(data)

        assert len(notifications) == 1
        assert notifications[0]["temperature"] == ""


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
