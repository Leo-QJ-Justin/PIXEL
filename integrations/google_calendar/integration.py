"""Google Calendar integration that alerts before upcoming events."""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer

from integrations.google_calendar.auth import load_credentials
from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)


class GoogleCalendarIntegration(BaseIntegration):
    """Polls Google Calendar and triggers alerts before upcoming events."""

    def __init__(self, integration_path: Path, settings: dict[str, Any]):
        super().__init__(integration_path, settings)
        self._timer: QTimer | None = None
        self._service = None
        self._alerted_event_ids: set[str] = set()
        self._running = False

    @property
    def name(self) -> str:
        return "google_calendar"

    @property
    def display_name(self) -> str:
        return "Google Calendar Alerts"

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": False,
            "check_interval_ms": 300000,
            "alert_before_minutes": 30,
            "trigger_behavior": "alert",
            "calendar_id": "primary",
        }

    async def start(self) -> None:
        """Start periodic calendar checking."""
        from config import BASE_DIR

        creds = await asyncio.to_thread(load_credentials, BASE_DIR)
        if creds is None:
            logger.error(
                "Google Calendar credentials not available — "
                "run 'uv run python scripts/auth_google_calendar.py' first"
            )
            return

        try:
            from googleapiclient.discovery import build

            self._service = await asyncio.to_thread(build, "calendar", "v3", credentials=creds)
        except Exception:
            logger.exception("Failed to build Google Calendar API service")
            return

        self._running = True
        interval = self._settings.get("check_interval_ms", 300000)

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start(interval)

        # Fetch immediately on start
        self._on_timer_tick()
        logger.info(
            f"Google Calendar integration started "
            f"(interval={interval}ms, "
            f"alert_before={self._settings.get('alert_before_minutes', 30)}min)"
        )

    async def stop(self) -> None:
        """Stop calendar checking."""
        self._running = False
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._service = None
        self._alerted_event_ids.clear()
        logger.info("Google Calendar integration stopped")

    def _on_timer_tick(self) -> None:
        """Timer callback — schedule async event check."""
        if not self._running:
            return
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._check_upcoming_events())
        except RuntimeError:
            logger.warning("No event loop available for calendar check")

    async def _check_upcoming_events(self) -> None:
        """Fetch upcoming events from Google Calendar."""
        if self._service is None:
            return

        alert_minutes = self._settings.get("alert_before_minutes", 30)
        calendar_id = self._settings.get("calendar_id", "primary")

        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        # Fetch a window slightly larger than alert_before_minutes
        from datetime import timedelta

        time_max = (now + timedelta(minutes=alert_minutes + 5)).isoformat()

        try:
            result = await asyncio.to_thread(
                lambda: self._service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=10,
                )
                .execute()
            )
        except Exception:
            logger.exception("Failed to fetch Google Calendar events")
            return

        events = result.get("items", [])
        self._process_events(events, now)

    def _process_events(self, events: list[dict], now: datetime) -> None:
        """Process events and trigger alerts for those within the alert window."""
        alert_minutes = self._settings.get("alert_before_minutes", 30)

        for event in events:
            event_id = event.get("id", "")
            if not event_id:
                continue

            start_data = event.get("start", {})
            event_time = self._parse_event_time(start_data)
            if event_time is None:
                continue

            # Skip events that have already started
            if event_time <= now:
                continue

            minutes_until = (event_time - now).total_seconds() / 60

            if minutes_until <= alert_minutes and event_id not in self._alerted_event_ids:
                self._alerted_event_ids.add(event_id)
                self._trigger_event_alert(event, minutes_until)

        self._cleanup_alerted_ids(events)

    def _trigger_event_alert(self, event: dict, minutes_until: float) -> None:
        """Trigger an alert behavior for an upcoming event."""
        summary = event.get("summary", "Untitled event")
        location = event.get("location", "")
        event_id = event.get("id", "")
        start_data = event.get("start", {})
        start_time = start_data.get("dateTime", start_data.get("date", ""))

        rounded_minutes = round(minutes_until)
        bubble_text = f"{summary} in {rounded_minutes} min"

        context = {
            "source": "google_calendar",
            "event_id": event_id,
            "summary": summary,
            "location": location,
            "start_time": start_time,
            "minutes_until": minutes_until,
            "bubble_text": bubble_text,
        }

        behavior = self._settings.get("trigger_behavior", "alert")
        self.trigger(behavior, context)
        logger.info(f"Calendar alert: {bubble_text}")

    @staticmethod
    def _parse_event_time(start_data: dict) -> datetime | None:
        """Parse event start time from Google Calendar API format.

        Handles both dateTime (with timezone) and date (all-day) formats.
        """
        if "dateTime" in start_data:
            try:
                return datetime.fromisoformat(start_data["dateTime"])
            except (ValueError, TypeError):
                return None

        if "date" in start_data:
            try:
                dt = datetime.strptime(start_data["date"], "%Y-%m-%d")
                return dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return None

        return None

    def _cleanup_alerted_ids(self, current_events: list[dict]) -> None:
        """Remove alerted IDs that are no longer in the upcoming events window."""
        current_ids = {e.get("id", "") for e in current_events}
        stale = self._alerted_event_ids - current_ids
        self._alerted_event_ids -= stale
