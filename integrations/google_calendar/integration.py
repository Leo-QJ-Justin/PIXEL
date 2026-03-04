"""Google Calendar integration — ambient reminders with day preview."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer

from config import BASE_DIR
from integrations.google_calendar.auth import load_credentials
from integrations.google_calendar.calendar_event import CalendarEvent
from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)


class GoogleCalendarIntegration(BaseIntegration):
    """Polls Google Calendar and triggers configurable reminders."""

    def __init__(self, integration_path: Path, settings: dict[str, Any]):
        super().__init__(integration_path, settings)
        self._timer: QTimer | None = None
        self._service = None
        self._running = False

        # Single source of truth for tracked events
        self._events: dict[str, CalendarEvent] = {}

        # Day preview fires once per start()
        self._day_preview_sent = False

    @property
    def name(self) -> str:
        return "google_calendar"

    @property
    def display_name(self) -> str:
        return "Google Calendar"

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": False,
            "check_interval_ms": 300_000,
            "calendar_id": "primary",
            "fetch_window_minutes": 120,
            "trigger_behavior": "alert",
            "reminder_minutes": [30, 5, 0],
            "day_preview_enabled": True,
        }

    # ── Lifecycle ──────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start periodic calendar checking."""
        creds = await asyncio.to_thread(load_credentials, BASE_DIR)
        if creds is None:
            logger.warning("Google Calendar credentials not available — integration dormant")
            return

        try:
            from googleapiclient.discovery import build

            self._service = await asyncio.to_thread(build, "calendar", "v3", credentials=creds)
        except Exception:
            logger.exception("Failed to build Google Calendar API service")
            return

        self._running = True
        self._day_preview_sent = False
        interval = self._settings.get("check_interval_ms", 300_000)

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start(interval)

        # Fetch immediately on start
        self._on_timer_tick()
        logger.info(
            f"Google Calendar integration started (interval={interval}ms, "
            f"window={self._settings.get('fetch_window_minutes', 120)}min)"
        )

    async def stop(self) -> None:
        """Stop calendar checking."""
        self._running = False
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._service = None
        self._events.clear()
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

    # ── Calendar Fetching ──────────────────────────────────────────────

    async def _check_upcoming_events(self) -> None:
        """Fetch upcoming events, process reminders, and emit day preview."""
        if self._service is None:
            return

        calendar_id = self._settings.get("calendar_id", "primary")
        fetch_window = self._settings.get("fetch_window_minutes", 120)

        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(minutes=fetch_window)).isoformat()

        try:
            result = await asyncio.to_thread(
                lambda: self._service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=20,
                )
                .execute()
            )
        except Exception:
            logger.exception("Failed to fetch Google Calendar events")
            return

        raw_events = result.get("items", [])

        # Upsert all events
        for raw in raw_events:
            self._upsert_event(raw)

        # Day preview on first successful fetch
        if not self._day_preview_sent and self._settings.get("day_preview_enabled", True):
            self._emit_day_preview(now)
            self._day_preview_sent = True

        # Process reminders
        for event in self._events.values():
            self._process_reminders(event, now)

        # Cleanup stale events
        self._cleanup_events(raw_events)

    # ── Event Upsert ──────────────────────────────────────────────────

    def _upsert_event(self, raw: dict) -> CalendarEvent | None:
        """Create or update a CalendarEvent from raw API data."""
        event_id = raw.get("id", "")
        if not event_id:
            return None

        start_data = raw.get("start", {})
        event_time = self._parse_event_time(start_data)
        if event_time is None:
            return None

        is_all_day = "date" in start_data and "dateTime" not in start_data
        summary = raw.get("summary", "Untitled event")
        location = raw.get("location") or None

        if event_id in self._events:
            event = self._events[event_id]
            if event.start_time != event_time:
                logger.info(f"Event '{summary}' start time changed, resetting alerts")
                event.reset_alerts()
                event.start_time = event_time
            event.summary = summary
            event.location = location
            event.is_all_day = is_all_day
            return event

        event = CalendarEvent(
            event_id=event_id,
            summary=summary,
            start_time=event_time,
            is_all_day=is_all_day,
            location=location,
        )
        self._events[event_id] = event
        return event

    # ── Reminders ──────────────────────────────────────────────────────

    def _process_reminders(self, event: CalendarEvent, now: datetime) -> None:
        """Fire reminder notifications for each configured interval."""
        if event.is_all_day or event.start_time <= now:
            return

        minutes_until = (event.start_time - now).total_seconds() / 60
        reminder_minutes = self._settings.get("reminder_minutes", [30, 5, 0])
        behavior = self._settings.get("trigger_behavior", "alert")

        for interval in sorted(reminder_minutes, reverse=True):
            if interval in event.alerted_intervals:
                continue
            # For interval 0 ("starting now"), fire when within 1 minute
            threshold = max(interval, 1)
            if minutes_until > threshold:
                continue

            event.alerted_intervals.add(interval)

            if interval == 0:
                bubble_text = f"{event.summary} starting now!"
                self.trigger(
                    behavior,
                    {
                        "source": "google_calendar",
                        "event_id": event.event_id,
                        "summary": event.summary,
                        "bubble_text": bubble_text,
                    },
                )
                logger.info(f"Calendar alert: {bubble_text}")
            else:
                bubble_text = f"{event.summary} in {interval} min"
                if interval <= 5:
                    bubble_text = f"{event.summary} in {interval} min!"
                self.notify(
                    {
                        "source": "google_calendar",
                        "event_id": event.event_id,
                        "summary": event.summary,
                        "bubble_text": bubble_text,
                    },
                )
                logger.info(f"Calendar reminder: {bubble_text}")

    # ── Day Preview ────────────────────────────────────────────────────

    def _emit_day_preview(self, now: datetime) -> None:
        """Build and emit a morning summary bubble."""
        today = now.date()

        today_events = [e for e in self._events.values() if e.start_time.date() == today]
        timed_events = [e for e in today_events if not e.is_all_day]
        all_day_events = [e for e in today_events if e.is_all_day]

        if not timed_events and not all_day_events:
            bubble_text = "No meetings today — free day!"
        elif not timed_events and all_day_events:
            if len(all_day_events) == 1:
                bubble_text = f"Just an all-day event today: {all_day_events[0].summary}."
            else:
                bubble_text = f"{len(all_day_events)} all-day events today."
        else:
            first = min(timed_events, key=lambda e: e.start_time)
            first_time = first.start_time.strftime("%I:%M %p").lstrip("0")
            count = len(timed_events)
            if count == 1:
                bubble_text = f"You have 1 meeting today: {first.summary} at {first_time}."
            else:
                bubble_text = (
                    f"You have {count} meetings today. "
                    f"First is {first.summary} at {first_time}."
                )

        self.notify({"bubble_text": bubble_text, "bubble_duration_ms": 8000})
        logger.info(f"Day preview: {bubble_text}")

    # ── Cleanup ────────────────────────────────────────────────────────

    def _cleanup_events(self, current_raw_events: list[dict]) -> None:
        """Remove CalendarEvent objects not in current fetch window."""
        current_ids = {e.get("id", "") for e in current_raw_events}
        stale = set(self._events.keys()) - current_ids
        for event_id in stale:
            del self._events[event_id]

    # ── Public API ─────────────────────────────────────────────────────

    def get_next_event(self) -> CalendarEvent | None:
        """Return the soonest upcoming non-all-day event, or None."""
        now = datetime.now(timezone.utc)
        candidates = [e for e in self._events.values() if not e.is_all_day and e.start_time > now]
        if not candidates:
            return None
        return min(candidates, key=lambda e: e.start_time)

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _parse_event_time(start_data: dict) -> datetime | None:
        """Parse event start time from Google Calendar API format."""
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
