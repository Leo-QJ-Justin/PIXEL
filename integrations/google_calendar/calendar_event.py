"""Calendar event model — single source of truth for per-event state."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GeocodedAddress:
    """Result of geocoding an address."""

    formatted_address: str
    lat: float
    lng: float


@dataclass
class TravelEstimate:
    """Travel time estimate for a single transport mode."""

    mode: str
    duration_minutes: float


@dataclass
class TravelInfo:
    """Aggregated travel info for an event destination."""

    location: str
    estimates: list[TravelEstimate]
    fetched_at: datetime

    @property
    def best_duration_minutes(self) -> float:
        """Return the shortest travel time across all modes."""
        if not self.estimates:
            return 0.0
        return min(e.duration_minutes for e in self.estimates)

    @property
    def best_mode(self) -> str:
        """Return the transport mode with the shortest travel time."""
        if not self.estimates:
            return ""
        return min(self.estimates, key=lambda e: e.duration_minutes).mode


# Patterns for virtual meeting locations
_VIRTUAL_PATTERNS = [
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"zoom\.us", re.IGNORECASE),
    re.compile(r"meet\.google\.com", re.IGNORECASE),
    re.compile(r"teams\.microsoft\.com", re.IGNORECASE),
    re.compile(r"webex\.com", re.IGNORECASE),
    re.compile(r"discord\.gg", re.IGNORECASE),
    re.compile(r"slack\.com", re.IGNORECASE),
]


def is_virtual_location(location: str) -> bool:
    """Check if a location string is a virtual meeting (Zoom, Meet, etc.)."""
    if not location:
        return False
    return any(p.search(location) for p in _VIRTUAL_PATTERNS)


@dataclass
class CalendarEvent:
    """Consolidates all per-event state for the Google Calendar integration."""

    # Identity & calendar data
    event_id: str
    summary: str
    start_time: datetime
    is_all_day: bool
    calendar_location: str | None = None

    # User interaction state
    user_location: str | None = None

    # Geocoding state
    geocoded_address: GeocodedAddress | None = None

    # Route confirmation state (smart origin detection)
    origin_address: str | None = None
    route_confirmed: bool = False
    route_declined: bool = False
    route_prompted: bool = False
    confirmed_origin: str | None = None
    confirmed_destination: str | None = None
    preferred_travel_mode: str | None = None

    # Travel state
    travel_info: TravelInfo | None = None

    # Two-fetch tracking
    initial_fetch_done: bool = False
    recheck_done: bool = False

    # Alert state
    prepare_alerted: bool = False
    leave_alerted: bool = False
    flat_alerted: bool = False

    @property
    def effective_location(self) -> str | None:
        """User-provided location takes precedence over calendar location."""
        return self.user_location or self.calendar_location

    @property
    def is_virtual(self) -> bool:
        """Check if location is a virtual meeting (Zoom, Meet, etc.)."""
        return is_virtual_location(self.effective_location or "")

    @property
    def needs_route_prompt(self) -> bool:
        """Whether this event should prompt the user to confirm a route.

        Fires even when no destination is set — the route dialog lets the
        user fill in both origin and destination in a single form.
        """
        return (
            not self.is_virtual
            and not self.is_all_day
            and not self.route_confirmed
            and not self.route_declined
            and not self.route_prompted
        )

    @property
    def needs_travel_fetch(self) -> bool:
        """Whether an automatic travel fetch is needed (initial fetch only).

        Rechecks are scheduled via QTimer, not driven by this property.
        """
        if not self.effective_location or self.is_all_day or self.is_virtual:
            return False
        if not self.route_confirmed:
            return False
        return not self.initial_fetch_done

    def reset_alerts(self) -> None:
        """Reset alert, route, and fetch state when event start_time changes."""
        self.prepare_alerted = False
        self.leave_alerted = False
        self.flat_alerted = False
        self.route_confirmed = False
        self.route_declined = False
        self.route_prompted = False
        self.confirmed_origin = None
        self.confirmed_destination = None
        self.initial_fetch_done = False
        self.recheck_done = False

    def to_persist_dict(self) -> dict:
        """Serialize user-interaction state for persistence (edge case #6).

        Travel info and alert state are transient — re-derived on restart.
        """
        return {
            "event_id": self.event_id,
            "user_location": self.user_location,
            "geocoded_lat": self.geocoded_address.lat if self.geocoded_address else None,
            "geocoded_lng": self.geocoded_address.lng if self.geocoded_address else None,
            "geocoded_formatted": (
                self.geocoded_address.formatted_address if self.geocoded_address else None
            ),
            "origin_address": self.origin_address,
            "route_confirmed": self.route_confirmed,
            "route_declined": self.route_declined,
            "confirmed_origin": self.confirmed_origin,
            "confirmed_destination": self.confirmed_destination,
            "preferred_travel_mode": self.preferred_travel_mode,
            "initial_fetch_done": self.initial_fetch_done,
            "recheck_done": self.recheck_done,
        }

    @staticmethod
    def restore_user_data(event: CalendarEvent, persisted: dict) -> None:
        """Restore user-interaction state from persisted data."""
        event.user_location = persisted.get("user_location")
        lat = persisted.get("geocoded_lat")
        lng = persisted.get("geocoded_lng")
        fmt = persisted.get("geocoded_formatted")
        if lat is not None and lng is not None and fmt:
            event.geocoded_address = GeocodedAddress(fmt, lat, lng)
        event.origin_address = persisted.get("origin_address")
        event.route_confirmed = persisted.get("route_confirmed", False)
        event.route_declined = persisted.get("route_declined", False)
        event.confirmed_origin = persisted.get("confirmed_origin")
        event.confirmed_destination = persisted.get("confirmed_destination")
        event.preferred_travel_mode = persisted.get("preferred_travel_mode")
        event.initial_fetch_done = persisted.get("initial_fetch_done", False)
        event.recheck_done = persisted.get("recheck_done", False)

        # Travel info is transient; if initial fetch was done but travel_info
        # is None (app restart), re-trigger the initial fetch
        if event.initial_fetch_done and event.travel_info is None:
            event.initial_fetch_done = False
