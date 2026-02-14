"""Google Routes API client for travel time estimation."""

import logging
from typing import TYPE_CHECKING

import aiohttp

from config import GOOGLE_MAPS_API_KEY
from integrations.google_calendar.calendar_event import TravelEstimate

if TYPE_CHECKING:
    from integrations.google_calendar.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

_ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


async def compute_travel_time(
    origin: str,
    destination: str,
    travel_modes: list[str],
    usage_tracker: "UsageTracker",
) -> list[TravelEstimate] | None:
    """Query Google Routes API for travel times across multiple modes.

    Returns a list of TravelEstimate or None if all queries fail.
    Each travel mode costs one API call.
    """
    if not GOOGLE_MAPS_API_KEY:
        return None

    estimates: list[TravelEstimate] = []

    for mode in travel_modes:
        if not usage_tracker.can_call("routes_api"):
            logger.warning("Google Routes API quota exhausted")
            break

        estimate = await _query_route(origin, destination, mode)
        if estimate is not None:
            usage_tracker.increment("routes_api")
            estimates.append(estimate)

    return estimates if estimates else None


async def _query_route(origin: str, destination: str, travel_mode: str) -> TravelEstimate | None:
    """Query a single route from the Google Routes API."""
    body: dict = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": travel_mode,
    }

    # Traffic-aware routing only for driving
    if travel_mode == "DRIVE":
        body["routingPreference"] = "TRAFFIC_AWARE"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "routes.duration",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(_ROUTES_API_URL, json=body, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Routes API error ({resp.status}) for {travel_mode}: {text}")
                    return None
                data = await resp.json()
                return _parse_route_response(data, travel_mode)
    except Exception:
        logger.exception(f"Routes API request failed for {travel_mode}")
        return None


def _parse_route_response(data: dict, travel_mode: str) -> TravelEstimate | None:
    """Parse a Routes API response into a TravelEstimate.

    Duration format from API: "1234s" (seconds as string).
    """
    routes = data.get("routes", [])
    if not routes:
        return None

    duration_str = routes[0].get("duration", "")
    if not duration_str:
        return None

    # Parse "1234s" → 1234 seconds → minutes
    try:
        seconds = int(duration_str.rstrip("s"))
        minutes = seconds / 60
        return TravelEstimate(mode=travel_mode, duration_minutes=minutes)
    except (ValueError, TypeError):
        logger.error(f"Could not parse duration: {duration_str}")
        return None
