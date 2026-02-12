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


class WeatherIntegration(BaseIntegration):
    """Fetches local weather and triggers rainy/sunny behaviors."""

    def __init__(self, integration_path: Path, settings: dict[str, Any]):
        super().__init__(integration_path, settings)
        self._timer: QTimer | None = None
        self._last_weather_behavior: str | None = None
        self._running = False

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
            "units": "imperial",
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

        # Fetch immediately on start
        self._on_timer_tick()
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
        units = self._settings.get("units", "imperial")

        params = {
            "q": city,
            "appid": api_key,
            "units": units,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, params=params) as resp:
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
        """Process weather API response and trigger appropriate behavior."""
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

            units = self._settings.get("units", "imperial")
            unit_label = "\u00b0F" if units == "imperial" else "\u00b0C"
            temperature = f"{temp}{unit_label}" if temp is not None else ""

            context = {
                "condition": behavior or "other",
                "description": description,
                "temperature": temperature,
                "city": city,
                "condition_id": condition_id,
            }

            # Only trigger if the weather condition changed
            if behavior and behavior != self._last_weather_behavior:
                self._last_weather_behavior = behavior
                self.trigger(behavior, context)
                logger.info(f"Weather changed to {behavior}: {description} in {city}")
            elif behavior is None and self._last_weather_behavior is not None:
                # Weather cleared — return to idle and reset tracking
                self._last_weather_behavior = None
                self.trigger("idle", context)
                logger.info(f"Weather cleared: {description} in {city}, returning to idle")

        except (KeyError, IndexError, TypeError):
            logger.exception("Failed to parse weather data")

    @staticmethod
    def _map_condition_to_behavior(condition_id: int) -> str | None:
        """Map OpenWeatherMap condition code to a behavior name.

        Condition code groups:
        - 2xx: Thunderstorm
        - 3xx: Drizzle
        - 5xx: Rain
        - 6xx: Snow
        - 800: Clear sky
        - 80x: Clouds
        - 7xx: Atmosphere (fog, mist, etc.)
        """
        group = condition_id // 100

        if group in (2, 3, 5, 6):
            return "rainy"
        if condition_id == 800:
            return "sunny"
        return None
