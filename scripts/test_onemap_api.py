"""Test script to make one call to the OneMap routing API.

Run this, then verify the token and routing response work correctly.

Usage:
    uv run python scripts/test_onemap_api.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("ONEMAP_EMAIL")
PASSWORD = os.getenv("ONEMAP_PASSWORD")

TOKEN_URL = "https://www.onemap.gov.sg/api/auth/post/getToken"
ROUTE_URL = "https://www.onemap.gov.sg/api/public/routingsvc/route"


async def get_token():
    """Authenticate and return a bearer token."""
    import aiohttp

    body = {"email": EMAIL, "password": PASSWORD}

    async with aiohttp.ClientSession() as session:
        async with session.post(TOKEN_URL, json=body) as resp:
            data = await resp.json()
            print(f"[Auth] Status: {resp.status}")
            if resp.status == 200:
                token = data.get("access_token")
                expiry = data.get("expiry_timestamp")
                print(f"  Token: {token[:20]}...{token[-10:]}" if token else "  Token: None")
                print(f"  Expires: {expiry}")
                return token
            else:
                print(f"  Error: {data}")
                return None


async def test_drive_route(token):
    """Make a drive routing call (Raffles Place -> Changi Airport)."""
    import aiohttp

    params = {
        "start": "1.2840,103.8514",  # Raffles Place
        "end": "1.3644,103.9915",  # Changi Airport
        "routeType": "drive",
    }
    headers = {"Authorization": token}

    async with aiohttp.ClientSession() as session:
        async with session.get(ROUTE_URL, params=params, headers=headers) as resp:
            data = await resp.json()
            print(f"[Drive Route] Status: {resp.status}")
            if resp.status == 200:
                summary = data.get("route_summary", {})
                total_time = summary.get("total_time", 0)
                total_dist = summary.get("total_distance", 0)
                print(f"  Duration: {total_time / 60:.1f} min ({total_time}s)")
                print(f"  Distance: {total_dist / 1000:.1f} km")
            else:
                print(f"  Error: {data}")


async def test_transit_route(token):
    """Make a public transport routing call (Raffles Place -> Changi Airport)."""
    from datetime import datetime

    import aiohttp

    now = datetime.now()
    params = {
        "start": "1.2840,103.8514",  # Raffles Place
        "end": "1.3644,103.9915",  # Changi Airport
        "routeType": "pt",
        "date": now.strftime("%m-%d-%Y"),
        "time": now.strftime("%H:%M:%S"),
        "mode": "TRANSIT",
    }
    headers = {"Authorization": token}

    async with aiohttp.ClientSession() as session:
        async with session.get(ROUTE_URL, params=params, headers=headers) as resp:
            data = await resp.json()
            print(f"[Transit Route] Status: {resp.status}")
            if resp.status == 200:
                plan = data.get("plan", {})
                itineraries = plan.get("itineraries", [])
                if itineraries:
                    duration = itineraries[0].get("duration", 0)
                    print(f"  Duration: {duration / 60:.1f} min ({duration}s)")
                    print(f"  Options: {len(itineraries)} itineraries returned")
                else:
                    print("  No itineraries returned")
            else:
                print(f"  Error: {data}")


async def main():
    if not EMAIL or not PASSWORD:
        print("ERROR: ONEMAP_EMAIL and ONEMAP_PASSWORD not set in .env")
        sys.exit(1)

    print(f"Using email: {EMAIL}\n")

    print("--- Authenticating ---")
    token = await get_token()
    if not token:
        print("\nAuthentication failed. Check your credentials.")
        sys.exit(1)

    print("\n--- Testing Drive Route (Raffles Place -> Changi Airport) ---")
    await test_drive_route(token)

    print("\n--- Testing Transit Route (Raffles Place -> Changi Airport) ---")
    await test_transit_route(token)

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
