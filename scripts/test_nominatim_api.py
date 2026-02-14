"""Test script to make one call to the OpenStreetMap Nominatim geocoding API.

Nominatim is free, no API key required. Rate limit: 1 request/sec.

Usage:
    uv run python scripts/test_nominatim_api.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def test_geocode(address):
    """Geocode an address using Nominatim."""
    import aiohttp

    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }
    headers = {
        "User-Agent": "HaroDesktopPet/1.0",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(NOMINATIM_URL, params=params, headers=headers) as resp:
            data = await resp.json()
            print(f"[Nominatim] Status: {resp.status}")
            if resp.status == 200 and data:
                result = data[0]
                print(f"  Query: {address}")
                print(f"  Address: {result.get('display_name', 'N/A')}")
                print(f"  Lat: {result.get('lat', 'N/A')}")
                print(f"  Lng: {result.get('lon', 'N/A')}")
                print(f"  Type: {result.get('type', 'N/A')}")
            elif resp.status == 200:
                print(f"  No results for: {address}")
            else:
                print(f"  Error: {data}")


async def main():
    print("--- Testing Nominatim Geocoding ---\n")

    print("Test 1: Street address")
    await test_geocode("Changi Airport, Singapore")

    # Respect 1 req/sec rate limit
    await asyncio.sleep(1)

    print("\nTest 2: General location")
    await test_geocode("Raffles Place, Singapore")

    print("\nDone!")
    print("Note: Nominatim enforces a 1 request/sec rate limit.")
    print("The app adds asyncio.sleep(1) between calls to respect this.")


if __name__ == "__main__":
    asyncio.run(main())
