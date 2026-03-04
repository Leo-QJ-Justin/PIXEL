"""Calendar event model — single source of truth for per-event state."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

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
    location: str | None = None

    # Tracks which reminder intervals (in minutes) have already fired
    alerted_intervals: set[int] = field(default_factory=set)

    @property
    def is_virtual(self) -> bool:
        """Check if location is a virtual meeting (Zoom, Meet, etc.)."""
        return is_virtual_location(self.location or "")

    def reset_alerts(self) -> None:
        """Reset alert state when event start_time changes."""
        self.alerted_intervals.clear()
