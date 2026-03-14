"""Weather integration that triggers behaviors based on local weather conditions."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import aiohttp
from PyQt6.QtCore import QTimer

from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)

API_URL = "https://api.openweathermap.org/data/2.5/weather"

_UNSET = object()  # sentinel for "haven't checked yet"


class WeatherIntegration(BaseIntegration):
    """Fetches local weather and triggers short reactions for precipitation."""

    def __init__(self, integration_path: Path, settings: dict[str, Any]):
        super().__init__(integration_path, settings)
        self._timer: QTimer | None = None
        self._last_condition: object = _UNSET
        self._running = False
        self._session: aiohttp.ClientSession | None = None

    @property
    def name(self) -> str:
        return "weather"

    @property
    def display_name(self) -> str:
        return "Weather Reactions"

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "city": "New York",
            "units": "metric",
            "check_interval_ms": 600000,
        }

    async def start(self) -> None:
        """Start periodic weather checking."""
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            logger.error("OPENWEATHER_API_KEY not configured in .env file")
            return

        self._running = True
        interval = self._settings.get("check_interval_ms", 1800000)

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start(interval)

        # Delay initial fetch so the startup greeting can play first
        QTimer.singleShot(5000, self._on_timer_tick)
        logger.info(
            f"Weather integration started (city={self._settings.get('city', 'New York')}, "
            f"interval={interval}ms)"
        )

    async def stop(self) -> None:
        """Stop weather checking."""
        self._running = False
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        logger.info("Weather integration stopped")

    def _on_timer_tick(self) -> None:
        """Timer callback — schedule async fetch on the running event loop."""
        if not self._running:
            return
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._fetch_weather())
        except RuntimeError:
            logger.warning("No event loop available for weather fetch")

    async def _fetch_weather(self) -> None:
        """Fetch weather data from OpenWeatherMap."""
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return

        city = self._settings.get("city", "New York")
        units = self._settings.get("units", "metric")

        params = {
            "q": city,
            "appid": api_key,
            "units": units,
        }

        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            async with self._session.get(API_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"Weather API returned status {resp.status}")
                    return
                data = await resp.json()
        except aiohttp.ClientError as e:
            logger.error(f"Weather API request failed: {e}")
            return
        except Exception:
            logger.exception("Unexpected error fetching weather")
            return

        self._process_weather_data(data)

    def _process_weather_data(self, data: dict) -> None:
        """Process weather API response and trigger appropriate behavior or notification."""
        try:
            weather_list = data.get("weather", [])
            if not weather_list:
                logger.warning("No weather data in API response")
                return

            condition_id = weather_list[0].get("id", 0)
            description = weather_list[0].get("description", "").capitalize()
            temp = data.get("main", {}).get("temp")
            city = data.get("name", "")

            behavior = self._map_condition_to_behavior(condition_id)

            units = self._settings.get("units", "metric")
            unit_label = "\u00b0F" if units == "imperial" else "\u00b0C"
            temperature = f"{temp}{unit_label}" if temp is not None else ""

            # Build bubble text: "Light rain, 25°C in Singapore"
            parts = [p for p in [description, temperature] if p]
            bubble_text = ", ".join(parts)
            if city:
                bubble_text += f" in {city}"

            context = {
                "condition": behavior or "other",
                "description": description,
                "temperature": temperature,
                "city": city,
                "condition_id": condition_id,
                "bubble_text": bubble_text,
            }

            # Only act on weather condition changes
            if behavior == self._last_condition:
                return  # same condition — skip

            self._last_condition = behavior

            if behavior:
                # Precipitation — play short reaction + show bubble
                self.trigger(behavior, context)
                logger.info(f"Weather changed to {behavior}: {description} in {city}")
            else:
                # Non-precipitation — bubble notification only
                self.notify(context)
                logger.info(f"Weather update: {description} in {city}")

        except (KeyError, IndexError, TypeError):
            logger.exception("Failed to parse weather data")

    @staticmethod
    def _map_condition_to_behavior(condition_id: int) -> str | None:
        """Map OpenWeatherMap condition code to a behavior name.

        Only precipitation triggers a behavior (short non-looping reaction).
        All other conditions are bubble-only notifications.

        Condition code groups:
        - 2xx: Thunderstorm
        - 3xx: Drizzle
        - 5xx: Rain
        - 6xx: Snow
        - 7xx: Atmosphere (fog, mist, etc.) — no behavior
        - 800: Clear sky — no behavior
        - 80x: Clouds — no behavior
        """
        group = condition_id // 100

        if group in (2, 3, 5, 6):
            return "rainy"
        return None
