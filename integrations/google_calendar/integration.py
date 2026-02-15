"""Google Calendar integration with two-phase travel-time-aware alerts."""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer, pyqtSignal

from config import BASE_DIR, GOOGLE_MAPS_API_KEY, ONEMAP_EMAIL, ONEMAP_PASSWORD
from integrations.google_calendar.auth import load_credentials
from integrations.google_calendar.calendar_event import (
    CalendarEvent,
    TravelInfo,
)
from integrations.google_calendar.geocoding import geocode_address
from integrations.google_calendar.onemap import compute_travel_time_onemap
from integrations.google_calendar.routes import compute_travel_time
from integrations.google_calendar.usage_tracker import UsageTracker
from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)

_EVENT_CACHE_FILE = BASE_DIR / "event_cache.json"


class GoogleCalendarIntegration(BaseIntegration):
    """Polls Google Calendar and triggers two-phase travel-aware alerts."""

    # Signal for route confirmation dialog (smart origin detection)
    request_route_confirmation = pyqtSignal(
        str, str, str, str
    )  # (event_id, origin, destination, mode)

    def __init__(self, integration_path: Path, settings: dict[str, Any]):
        super().__init__(integration_path, settings)
        self._timer: QTimer | None = None
        self._service = None
        self._running = False

        # Single source of truth for all event state
        self._events: dict[str, CalendarEvent] = {}

        # Smart origin: remember last confirmed origin across events
        self._last_confirmed_origin: str | None = None

        # API quota tracker
        quota_limit = self._settings.get("api_quota_limit", 9500)
        self._usage_tracker = UsageTracker(quota_limit=quota_limit)

        # Load persisted user-interaction state (edge case #6)
        self._persisted_data: dict[str, dict] = {}
        self._load_event_cache()

    @property
    def name(self) -> str:
        return "google_calendar"

    @property
    def display_name(self) -> str:
        return "Google Calendar Alerts"

    @property
    def usage_tracker(self) -> UsageTracker:
        """Expose usage tracker for tray icon display."""
        return self._usage_tracker

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": False,
            "check_interval_ms": 300000,
            "alert_before_minutes": 30,
            "trigger_behavior": "alert",
            "calendar_id": "primary",
            "origin_address": "",
            "preparation_minutes": 15,
            "travel_modes": ["DRIVE", "TRANSIT"],
            "travel_cache_ttl_minutes": 30,
            "fetch_window_minutes": 120,
            "api_quota_limit": 9500,
        }

    async def start(self) -> None:
        """Start periodic calendar checking."""
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
            f"fetch_window={self._settings.get('fetch_window_minutes', 120)}min)"
        )

    async def stop(self) -> None:
        """Stop calendar checking and persist state."""
        self._running = False
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._service = None
        self._save_event_cache()
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

    def _has_routing_provider(self) -> bool:
        """Check if any routing provider (Google Maps or OneMap) is configured."""
        return bool(GOOGLE_MAPS_API_KEY) or bool(ONEMAP_EMAIL and ONEMAP_PASSWORD)

    # ── Calendar Fetching ──────────────────────────────────────────────

    async def _check_upcoming_events(self) -> None:
        """Fetch upcoming events from Google Calendar."""
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
        await self._process_events(raw_events, now)

    # ── Event Processing ───────────────────────────────────────────────

    async def _process_events(self, raw_events: list[dict], now: datetime) -> None:
        """Process events: route prompts, two-phase alerts, flat fallback."""
        for raw in raw_events:
            event = self._upsert_event(raw)
            if event is None:
                continue

            # Skip events that have started
            if event.start_time <= now:
                continue

            minutes_until = (event.start_time - now).total_seconds() / 60

            # Route confirmation path (smart origin detection)
            # When a routing provider is available, use the route dialog for
            # both origin and destination — even if the event has no location yet.
            if not event.is_virtual and not event.is_all_day and self._has_routing_provider():
                # Route already confirmed → fetch travel and do two-phase alerts
                if event.route_confirmed:
                    origin = event.origin_address or ""
                    if event.needs_travel_fetch and origin:
                        await self._fetch_travel_info(event, origin)

                    if event.travel_info:
                        travel = event.travel_info.best_duration_minutes
                        prep = self._settings.get("preparation_minutes", 15)

                        # Warn if travel + prep exceeds fetch window (edge case #4)
                        fetch_window = self._settings.get("fetch_window_minutes", 120)
                        if travel + prep > fetch_window:
                            logger.warning(
                                f"Travel+prep ({travel + prep:.0f} min) exceeds "
                                f"fetch window ({fetch_window} min) for '{event.summary}'"
                            )

                        # Phase 1: Prepare alert — bubble only (edge case #1)
                        if minutes_until <= travel + prep and not event.prepare_alerted:
                            event.prepare_alerted = True
                            leave_in = round(minutes_until - travel)
                            self._notify_prepare(event, leave_in)

                        # Phase 2: Leave alert — full alert behavior
                        if minutes_until <= travel and not event.leave_alerted:
                            event.leave_alerted = True
                            self._trigger_leave_alert(
                                event,
                                round(travel),
                                event.travel_info.best_mode,
                            )

                        continue  # skip flat alert

                # Not yet confirmed/declined → show route prompt bubble
                elif event.needs_route_prompt:
                    event.route_prompted = True
                    self._notify_route_prompt(event)
                    continue

            # Flat fallback (no routing provider, declined, or no travel info)
            alert_minutes = self._settings.get("alert_before_minutes", 30)
            if minutes_until <= alert_minutes and not event.flat_alerted:
                event.flat_alerted = True
                self._trigger_flat_alert(event, minutes_until)

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

        cache_ttl = self._settings.get("travel_cache_ttl_minutes", 30)

        if event_id in self._events:
            event = self._events[event_id]
            # Check for start_time change (edge case #11)
            if event.start_time != event_time:
                logger.info(f"Event '{summary}' start time changed, resetting alerts")
                event.reset_alerts()
                event.start_time = event_time
            event.summary = summary
            event.calendar_location = location
            event.is_all_day = is_all_day
            return event

        # New event
        event = CalendarEvent(
            event_id=event_id,
            summary=summary,
            start_time=event_time,
            is_all_day=is_all_day,
            calendar_location=location,
            _travel_cache_ttl_minutes=cache_ttl,
        )

        # Restore persisted user data if available (edge case #6)
        if event_id in self._persisted_data:
            CalendarEvent.restore_user_data(event, self._persisted_data[event_id])

        self._events[event_id] = event
        return event

    # ── Travel Info Fetching ──────────────────────────────────────────

    async def _fetch_travel_info(self, event: CalendarEvent, origin: str) -> None:
        """Fetch travel time using cascading providers: Google → OneMap → skip."""
        destination = event.effective_location
        if not destination:
            return

        # Use only the user's preferred mode if set, otherwise all configured
        if event.preferred_travel_mode:
            travel_modes = [event.preferred_travel_mode]
        else:
            travel_modes = self._settings.get("travel_modes", ["DRIVE", "TRANSIT"])

        # 1. Try Google Routes API (if key set + quota available)
        if GOOGLE_MAPS_API_KEY:
            estimates = await compute_travel_time(
                origin, destination, travel_modes, self._usage_tracker
            )
            if estimates:
                event.travel_info = TravelInfo(
                    location=destination,
                    estimates=estimates,
                    fetched_at=datetime.now(timezone.utc),
                )
                return

        # 2. Try OneMap (if credentials set)
        if ONEMAP_EMAIL and ONEMAP_PASSWORD:
            await self._fetch_via_onemap(event, origin, destination, travel_modes)
            if event.travel_info:
                return

        # 3. Both unavailable — log and fall through to flat alert
        logger.debug(
            f"No routing provider available for '{event.summary}', " f"will use flat alert"
        )

    async def _fetch_via_onemap(
        self,
        event: CalendarEvent,
        origin: str,
        destination: str,
        travel_modes: list[str],
    ) -> None:
        """Fetch travel time via OneMap (needs lat/lng from geocoding)."""
        # Geocode origin
        origin_geo = await geocode_address(origin, self._usage_tracker)
        if origin_geo is None:
            logger.warning(f"Could not geocode origin: {origin}")
            return

        # Geocode destination (use cached geocoded_address if available)
        if event.geocoded_address:
            dest_geo = event.geocoded_address
        else:
            dest_geo = await geocode_address(destination, self._usage_tracker)
            if dest_geo is None:
                logger.warning(f"Could not geocode destination: {destination}")
                return
            event.geocoded_address = dest_geo

        estimates = await compute_travel_time_onemap(
            origin_geo.lat,
            origin_geo.lng,
            dest_geo.lat,
            dest_geo.lng,
            travel_modes,
        )
        if estimates:
            event.travel_info = TravelInfo(
                location=destination,
                estimates=estimates,
                fetched_at=datetime.now(timezone.utc),
            )

    # ── Alert Methods ─────────────────────────────────────────────────

    def _notify_prepare(self, event: CalendarEvent, leave_in: int) -> None:
        """Phase 1: bubble-only notification (no behavior change, edge case #1)."""
        bubble_text = f"Get ready! {event.summary} — leave in {leave_in} min"
        self.notify(
            {
                "source": "google_calendar",
                "action": "prepare",
                "event_id": event.event_id,
                "bubble_text": bubble_text,
            }
        )
        logger.info(f"Prepare alert: {bubble_text}")

    def _trigger_leave_alert(
        self, event: CalendarEvent, travel_minutes: int, travel_mode: str
    ) -> None:
        """Phase 2: full alert behavior with bounce + sound."""
        bubble_text = f"Time to go! {event.summary} ({travel_minutes} min {travel_mode.lower()})"
        context = {
            "source": "google_calendar",
            "event_id": event.event_id,
            "summary": event.summary,
            "location": event.effective_location or "",
            "travel_minutes": travel_minutes,
            "travel_mode": travel_mode,
            "bubble_text": bubble_text,
        }
        behavior = self._settings.get("trigger_behavior", "alert")
        self.trigger(behavior, context)
        logger.info(f"Leave alert: {bubble_text}")

    def _trigger_flat_alert(self, event: CalendarEvent, minutes_until: float) -> None:
        """Flat fallback alert (no travel info available)."""
        rounded_minutes = round(minutes_until)
        bubble_text = f"{event.summary} in {rounded_minutes} min"
        context = {
            "source": "google_calendar",
            "event_id": event.event_id,
            "summary": event.summary,
            "location": event.effective_location or "",
            "minutes_until": minutes_until,
            "bubble_text": bubble_text,
        }
        behavior = self._settings.get("trigger_behavior", "alert")
        self.trigger(behavior, context)
        logger.info(f"Calendar alert: {bubble_text}")

    def _notify_route_prompt(self, event: CalendarEvent) -> None:
        """Prompt user to confirm route for an event (smart origin detection)."""
        bubble_text = f"{event.summary} coming up — click me to set route"
        self.notify(
            {
                "source": "google_calendar",
                "action": "request_route",
                "event_id": event.event_id,
                "summary": event.summary,
                "origin": self._last_confirmed_origin or "",
                "destination": event.effective_location or "",
                "travel_modes": self._settings.get("travel_modes", ["DRIVE", "TRANSIT"]),
                "bubble_text": bubble_text,
            }
        )
        logger.info(f"Route prompt: {event.summary}")

    # ── Route Confirmation Flow (smart origin detection) ─────────────

    def receive_route(self, event_id: str, origin: str, destination: str, mode: str) -> None:
        """Handle user-confirmed route — geocode both addresses and verify."""
        event = self._events.get(event_id)
        if not event:
            logger.warning(f"receive_route: unknown event {event_id}")
            return

        event.preferred_travel_mode = mode

        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._geocode_route(event, origin, destination))
        except RuntimeError:
            logger.warning("No event loop for route geocoding")

    async def _geocode_route(self, event: CalendarEvent, origin: str, destination: str) -> None:
        """Geocode both origin and destination, then emit verification signal."""
        origin_geo = await geocode_address(origin, self._usage_tracker)
        if origin_geo is None:
            logger.warning(f"Could not geocode origin: {origin}")
            self.notify(
                {
                    "source": "google_calendar",
                    "action": "geocode_error",
                    "event_id": event.event_id,
                    "field": "origin",
                    "bubble_text": "Couldn't find that origin address. Try again?",
                }
            )
            # Reset so user can retry
            event.route_prompted = False
            return

        dest_geo = await geocode_address(destination, self._usage_tracker)
        if dest_geo is None:
            logger.warning(f"Could not geocode destination: {destination}")
            self.notify(
                {
                    "source": "google_calendar",
                    "action": "geocode_error",
                    "event_id": event.event_id,
                    "field": "destination",
                    "bubble_text": "Couldn't find that destination address. Try again?",
                }
            )
            event.route_prompted = False
            return

        # Store geocoded addresses for verification
        event.confirmed_origin = origin_geo.formatted_address
        event.confirmed_destination = dest_geo.formatted_address
        event.origin_address = origin

        # If the event had no calendar location, store the user-provided destination
        if not event.effective_location:
            event.user_location = destination

        self.request_route_confirmation.emit(
            event.event_id,
            origin_geo.formatted_address,
            dest_geo.formatted_address,
            event.preferred_travel_mode or "",
        )

    def confirm_route(self, event_id: str) -> None:
        """User confirmed the geocoded route (FROM → TO)."""
        event = self._events.get(event_id)
        if not event:
            return

        event.route_confirmed = True
        self._last_confirmed_origin = event.origin_address
        self._save_event_cache()
        logger.info(
            f"Route confirmed for '{event.summary}': "
            f"{event.confirmed_origin} → {event.confirmed_destination}"
        )

        # Immediately fetch travel time and notify user with the estimate
        origin = event.origin_address or ""
        if origin and event.needs_travel_fetch:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._fetch_and_notify_travel(event, origin))
            except RuntimeError:
                logger.warning("No event loop for immediate travel fetch")

    async def _fetch_and_notify_travel(self, event: CalendarEvent, origin: str) -> None:
        """Fetch travel info and show a bubble with the estimated time."""
        await self._fetch_travel_info(event, origin)
        if event.travel_info:
            minutes = round(event.travel_info.best_duration_minutes)
            mode = event.travel_info.best_mode.lower()
            bubble_text = f"Route set! {event.summary} — {minutes} min by {mode}"
            self.notify(
                {
                    "source": "google_calendar",
                    "action": "travel_estimate",
                    "event_id": event.event_id,
                    "bubble_text": bubble_text,
                }
            )
            logger.info(f"Travel estimate: {bubble_text}")

    def reject_route(self, event_id: str) -> None:
        """User clicked 'No, edit' on route verification — allow re-prompt."""
        event = self._events.get(event_id)
        if not event:
            return
        event.route_prompted = False
        logger.info(f"Route rejected for '{event.summary}', allowing re-prompt")

    def skip_route(self, event_id: str) -> None:
        """User skipped routing for this event — use flat alert."""
        event = self._events.get(event_id)
        if not event:
            return
        event.route_declined = True
        logger.info(f"Route skipped for '{event.summary}', will use flat alert")

    # ── Event Cache Persistence (edge case #6) ────────────────────────

    def _load_event_cache(self) -> None:
        """Load persisted user-interaction state from event_cache.json."""
        if not _EVENT_CACHE_FILE.exists():
            return
        try:
            with open(_EVENT_CACHE_FILE) as f:
                data = json.load(f)
            self._persisted_data = {item["event_id"]: item for item in data if "event_id" in item}
            logger.debug(f"Loaded {len(self._persisted_data)} cached events")
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupted event_cache.json, starting fresh")

    def _save_event_cache(self) -> None:
        """Save user-interaction state for all tracked events."""
        items = [
            event.to_persist_dict()
            for event in self._events.values()
            if event.user_location or event.route_confirmed or event.route_declined
        ]
        try:
            with open(_EVENT_CACHE_FILE, "w") as f:
                json.dump(items, f, indent=2)
        except OSError:
            logger.exception("Failed to save event_cache.json")

    # ── Cleanup ───────────────────────────────────────────────────────

    def _cleanup_events(self, current_raw_events: list[dict]) -> None:
        """Remove CalendarEvent objects not in current fetch window."""
        current_ids = {e.get("id", "") for e in current_raw_events}
        stale = set(self._events.keys()) - current_ids
        for event_id in stale:
            del self._events[event_id]

    # ── Helpers ───────────────────────────────────────────────────────

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
