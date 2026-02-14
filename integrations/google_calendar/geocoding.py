"""Geocoding module — Google Geocoding API with Nominatim fallback."""

import asyncio
import logging
from typing import TYPE_CHECKING

import aiohttp

from config import GOOGLE_MAPS_API_KEY
from integrations.google_calendar.calendar_event import GeocodedAddress

if TYPE_CHECKING:
    from integrations.google_calendar.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

_GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "HaroDesktopPet/1.0"


async def geocode_address(address: str, usage_tracker: "UsageTracker") -> GeocodedAddress | None:
    """Geocode an address using Google Geocoding API with Nominatim fallback.

    Cascade: Google (if key + quota) → Nominatim (free) → None.
    """
    # Try Google first
    if GOOGLE_MAPS_API_KEY and usage_tracker.can_call("geocoding_api"):
        result = await _geocode_google(address)
        if result is not None:
            usage_tracker.increment("geocoding_api")
            return result
        # Google failed — fall through to Nominatim

    # Nominatim fallback
    return await _geocode_nominatim(address)


async def _geocode_google(address: str) -> GeocodedAddress | None:
    """Geocode using Google Geocoding API."""
    params = {"address": address, "key": GOOGLE_MAPS_API_KEY}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(_GOOGLE_GEOCODE_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"Google Geocoding API error ({resp.status})")
                    return None
                data = await resp.json()

                results = data.get("results", [])
                if not results:
                    return None

                top = results[0]
                location = top.get("geometry", {}).get("location", {})
                return GeocodedAddress(
                    formatted_address=top.get("formatted_address", address),
                    lat=location.get("lat", 0.0),
                    lng=location.get("lng", 0.0),
                )
    except Exception:
        logger.exception("Google Geocoding request failed")
        return None


async def _geocode_nominatim(address: str) -> GeocodedAddress | None:
    """Geocode using OpenStreetMap Nominatim (free, 1 req/sec rate limit)."""
    # Respect rate limit (edge case #8)
    await asyncio.sleep(1)

    params = {"q": address, "format": "json", "limit": "1"}
    headers = {"User-Agent": _USER_AGENT}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(_NOMINATIM_URL, params=params, headers=headers) as resp:
                if resp.status != 200:
                    logger.error(f"Nominatim API error ({resp.status})")
                    return None
                data = await resp.json()

                if not data:
                    return None

                top = data[0]
                return GeocodedAddress(
                    formatted_address=top.get("display_name", address),
                    lat=float(top.get("lat", 0)),
                    lng=float(top.get("lon", 0)),
                )
    except Exception:
        logger.exception("Nominatim geocoding request failed")
        return None
