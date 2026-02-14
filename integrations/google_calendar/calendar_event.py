"""Calendar event model — single source of truth for per-event state."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


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
    location_declined: bool = False
    location_prompted: bool = False

    # Geocoding state
    geocoded_address: GeocodedAddress | None = None
    geocode_confirmed: bool = False

    # Travel state
    travel_info: TravelInfo | None = None

    # Alert state
    prepare_alerted: bool = False
    leave_alerted: bool = False
    flat_alerted: bool = False

    # Config (injected at creation, not persisted)
    _travel_cache_ttl_minutes: int = field(default=30, repr=False)

    @property
    def effective_location(self) -> str | None:
        """User-provided location takes precedence over calendar location."""
        return self.user_location or self.calendar_location

    @property
    def is_virtual(self) -> bool:
        """Check if location is a virtual meeting (Zoom, Meet, etc.)."""
        return is_virtual_location(self.effective_location or "")

    @property
    def needs_location_prompt(self) -> bool:
        """Whether this event should prompt the user for a location."""
        return (
            not self.effective_location
            and not self.location_declined
            and not self.location_prompted
            and not self.is_all_day
        )

    @property
    def needs_travel_fetch(self) -> bool:
        """Whether travel info needs to be fetched or refreshed."""
        if not self.effective_location or self.is_all_day or self.is_virtual:
            return False
        if self.travel_info is None:
            return True
        return self._is_travel_stale()

    def _is_travel_stale(self) -> bool:
        """Check if cached travel info is stale (adaptive TTL, edge case #9)."""
        if self.travel_info is None:
            return True

        now = datetime.now(timezone.utc)
        age_minutes = (now - self.travel_info.fetched_at).total_seconds() / 60

        # Standard TTL check
        if age_minutes >= self._travel_cache_ttl_minutes:
            return True

        # Adaptive: force re-fetch when event is within 1.5x travel time
        minutes_until = (self.start_time - now).total_seconds() / 60
        if minutes_until <= self.travel_info.best_duration_minutes * 1.5:
            return True

        return False

    def reset_alerts(self) -> None:
        """Reset alert state when event start_time changes (edge case #11)."""
        self.prepare_alerted = False
        self.leave_alerted = False
        self.flat_alerted = False

    def to_persist_dict(self) -> dict:
        """Serialize user-interaction state for persistence (edge case #6).

        Travel info and alert state are transient — re-derived on restart.
        """
        return {
            "event_id": self.event_id,
            "user_location": self.user_location,
            "location_declined": self.location_declined,
            "geocoded_lat": self.geocoded_address.lat if self.geocoded_address else None,
            "geocoded_lng": self.geocoded_address.lng if self.geocoded_address else None,
            "geocoded_formatted": (
                self.geocoded_address.formatted_address if self.geocoded_address else None
            ),
            "geocode_confirmed": self.geocode_confirmed,
        }

    @staticmethod
    def restore_user_data(event: CalendarEvent, persisted: dict) -> None:
        """Restore user-interaction state from persisted data."""
        event.user_location = persisted.get("user_location")
        event.location_declined = persisted.get("location_declined", False)
        event.geocode_confirmed = persisted.get("geocode_confirmed", False)
        lat = persisted.get("geocoded_lat")
        lng = persisted.get("geocoded_lng")
        fmt = persisted.get("geocoded_formatted")
        if lat is not None and lng is not None and fmt:
            event.geocoded_address = GeocodedAddress(fmt, lat, lng)
