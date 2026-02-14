"""OneMap Singapore routing client — free fallback for travel time estimation."""

import logging
from datetime import datetime

import aiohttp

from config import ONEMAP_EMAIL, ONEMAP_PASSWORD
from integrations.google_calendar.calendar_event import TravelEstimate

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://www.onemap.gov.sg/api/auth/post/getToken"
_ROUTE_URL = "https://www.onemap.gov.sg/api/public/routingsvc/route"

# Map Google travel mode names to OneMap routeType values
_MODE_MAP = {
    "DRIVE": "drive",
    "TRANSIT": "pt",
    "WALK": "walk",
    "BICYCLE": "cycle",
}

# Cached token state
_cached_token: str | None = None
_token_expiry: datetime | None = None


async def get_onemap_token() -> str | None:
    """Authenticate with OneMap and return a bearer token.

    Tokens are valid for 3 days; cached in-memory.
    """
    global _cached_token, _token_expiry

    if _cached_token and _token_expiry and datetime.now() < _token_expiry:
        return _cached_token

    if not ONEMAP_EMAIL or not ONEMAP_PASSWORD:
        return None

    body = {"email": ONEMAP_EMAIL, "password": ONEMAP_PASSWORD}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(_TOKEN_URL, json=body) as resp:
                if resp.status != 200:
                    logger.error(f"OneMap auth failed ({resp.status})")
                    return None
                data = await resp.json()
                token = data.get("access_token")
                expiry = data.get("expiry_timestamp")
                if not token:
                    logger.error("OneMap auth response missing access_token")
                    return None

                _cached_token = token
                if expiry:
                    try:
                        _token_expiry = datetime.fromtimestamp(float(expiry))
                    except (ValueError, TypeError):
                        # Default to 3 days if parsing fails
                        from datetime import timedelta

                        _token_expiry = datetime.now() + timedelta(days=3)
                else:
                    from datetime import timedelta

                    _token_expiry = datetime.now() + timedelta(days=3)

                return _cached_token
    except Exception:
        logger.exception("OneMap authentication request failed")
        return None


async def compute_travel_time_onemap(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    travel_modes: list[str],
) -> list[TravelEstimate] | None:
    """Query OneMap routing API for travel times.

    Requires lat/lng coordinates (geocode addresses first via Nominatim).
    """
    token = await get_onemap_token()
    if not token:
        return None

    estimates: list[TravelEstimate] = []

    for mode in travel_modes:
        onemap_mode = _MODE_MAP.get(mode)
        if not onemap_mode:
            logger.debug(f"Skipping unsupported OneMap mode: {mode}")
            continue

        estimate = await _query_onemap_route(
            token, origin_lat, origin_lng, dest_lat, dest_lng, mode, onemap_mode
        )
        if estimate is not None:
            estimates.append(estimate)

    return estimates if estimates else None


async def _query_onemap_route(
    token: str,
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    google_mode: str,
    onemap_mode: str,
) -> TravelEstimate | None:
    """Query a single route from OneMap."""
    params: dict = {
        "start": f"{origin_lat},{origin_lng}",
        "end": f"{dest_lat},{dest_lng}",
        "routeType": onemap_mode,
    }

    # Public transport requires additional params
    if onemap_mode == "pt":
        now = datetime.now()
        params["date"] = now.strftime("%m-%d-%Y")
        params["time"] = now.strftime("%H:%M:%S")
        params["mode"] = "TRANSIT"

    headers = {"Authorization": token}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(_ROUTE_URL, params=params, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"OneMap route error ({resp.status}) for {google_mode}: {text}")
                    return None
                data = await resp.json()
                return _parse_onemap_response(data, google_mode)
    except Exception:
        logger.exception(f"OneMap route request failed for {google_mode}")
        return None


def _parse_onemap_response(data: dict, travel_mode: str) -> TravelEstimate | None:
    """Parse OneMap route response into a TravelEstimate."""
    # OneMap returns route_summary with total_time in seconds
    route_summary = data.get("route_summary")
    if not route_summary:
        # PT mode uses a different response structure
        plan = data.get("plan", {})
        itineraries = plan.get("itineraries", [])
        if itineraries:
            duration_secs = itineraries[0].get("duration", 0)
            return TravelEstimate(mode=travel_mode, duration_minutes=duration_secs / 60)
        return None

    total_time = route_summary.get("total_time", 0)
    if not total_time:
        return None

    return TravelEstimate(mode=travel_mode, duration_minutes=total_time / 60)
