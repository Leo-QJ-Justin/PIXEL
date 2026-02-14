"""Test script to make one call to each Google Maps API.

Run this, then check Google Cloud Console > APIs & Services > Metrics
to see which quota buckets were hit.

Usage:
    uv run python scripts/test_google_maps_apis.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


async def test_routes_api():
    """Make a single Routes API call."""
    import aiohttp

    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters",
    }
    body = {
        "origin": {"address": "Singapore"},
        "destination": {"address": "Changi Airport, Singapore"},
        "travelMode": "DRIVE",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=body, headers=headers) as resp:
            data = await resp.json()
            print(f"[Routes API] Status: {resp.status}")
            if resp.status == 200:
                route = data.get("routes", [{}])[0]
                print(f"  Duration: {route.get('duration', 'N/A')}")
                print(f"  Distance: {route.get('distanceMeters', 'N/A')} meters")
            else:
                print(f"  Error: {data}")


async def test_geocoding_api():
    """Make a single Geocoding API call."""
    import aiohttp

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": "Changi Airport, Singapore",
        "key": API_KEY,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            print(f"[Geocoding API] Status: {resp.status}")
            status = data.get("status")
            print(f"  API Status: {status}")
            if status == "OK":
                result = data["results"][0]
                loc = result["geometry"]["location"]
                print(f"  Address: {result['formatted_address']}")
                print(f"  Lat/Lng: {loc['lat']}, {loc['lng']}")
            else:
                print(f"  Error: {data.get('error_message', status)}")


async def main():
    if not API_KEY:
        print("ERROR: GOOGLE_MAPS_API_KEY not set in .env")
        sys.exit(1)

    print(f"Using API key: {API_KEY[:8]}...{API_KEY[-4:]}\n")

    print("--- Testing Routes API ---")
    await test_routes_api()

    print("\n--- Testing Geocoding API ---")
    await test_geocoding_api()

    print("\nDone! Check Google Cloud Console > APIs & Services > Metrics")
    print("to see which quota buckets received requests.")


if __name__ == "__main__":
    asyncio.run(main())
