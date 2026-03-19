"""Test script — fetch upcoming Google Calendar events and print raw API response.

Usage:
    uv run python scripts/test_google_calendar.py
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    from integrations.google_calendar.auth import load_credentials

    creds = load_credentials(BASE_DIR)
    if creds is None:
        print(
            "ERROR: No valid credentials. Run 'uv run python scripts/auth_google_calendar.py' first."
        )
        return

    from googleapiclient.discovery import build

    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc)
    local_now = datetime.now().astimezone()
    fetch_window = 120  # minutes

    time_min = now.isoformat()
    time_max = (now + timedelta(minutes=fetch_window)).isoformat()

    print(f"Local time:  {local_now.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")
    print(f"UTC time:    {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"timeMin:     {time_min}")
    print(f"timeMax:     {time_max}")
    print(f"Window:      {fetch_window} minutes")
    print("Calendar ID: primary")
    print("-" * 60)

    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=20,
        )
        .execute()
    )

    # Calendar metadata
    print(f"Calendar:    {result.get('summary', '?')}")
    print(f"Timezone:    {result.get('timeZone', '?')}")
    print(f"Updated:     {result.get('updated', '?')}")
    print("-" * 60)

    items = result.get("items", [])
    if not items:
        print("No events found in window.")
        print()
        print("Troubleshooting:")
        print("  1. Is the event on the 'primary' calendar (not a secondary/shared one)?")
        print("  2. Does the event start within the next 2 hours?")
        print(
            f"  3. Calendar timezone is '{result.get('timeZone')}' — does that match your actual timezone?"
        )
        print("     If your calendar timezone is UTC but you're in e.g. UTC+8,")
        print("     events may appear at unexpected absolute times.")
        print(
            f"  4. Query window: {local_now.strftime('%H:%M')} – {(local_now + timedelta(minutes=fetch_window)).strftime('%H:%M')} local time"
        )
    else:
        print(f"Found {len(items)} event(s):\n")
        for i, event in enumerate(items, 1):
            start = event.get("start", {})
            start_str = start.get("dateTime", start.get("date", "?"))
            print(f"  [{i}] {event.get('summary', 'Untitled')}")
            print(f"      Start:    {start_str}")
            print(f"      Location: {event.get('location', '(none)')}")
            print(f"      Status:   {event.get('status', '?')}")
            print(f"      ID:       {event.get('id', '?')}")
            print()

    # Also try fetching ALL calendars to check if event is on a different one
    print("-" * 60)
    print("All calendars on this account:")
    cal_list = service.calendarList().list().execute()
    for cal in cal_list.get("items", []):
        primary = " (PRIMARY)" if cal.get("primary") else ""
        print(f"  - {cal.get('summary', '?')} [{cal.get('id')}] tz={cal.get('timeZone')}{primary}")


if __name__ == "__main__":
    main()
