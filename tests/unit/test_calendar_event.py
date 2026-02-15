"""Tests for CalendarEvent model."""

from datetime import datetime, timedelta, timezone

import pytest


def _make_event(**kwargs):
    """Helper to create a CalendarEvent with sensible defaults."""
    from integrations.google_calendar.calendar_event import CalendarEvent

    defaults = {
        "event_id": "test-evt-1",
        "summary": "Test Meeting",
        "start_time": datetime.now(timezone.utc) + timedelta(hours=1),
        "is_all_day": False,
    }
    defaults.update(kwargs)
    return CalendarEvent(**defaults)


@pytest.mark.unit
class TestEffectiveLocation:
    """Tests for effective_location property."""

    def test_returns_user_location_over_calendar_location(self):
        event = _make_event(
            calendar_location="Calendar Room A",
            user_location="User Room B",
        )
        assert event.effective_location == "User Room B"

    def test_returns_calendar_location_when_no_user_location(self):
        event = _make_event(
            calendar_location="Calendar Room A",
            user_location=None,
        )
        assert event.effective_location == "Calendar Room A"

    def test_returns_none_when_no_location(self):
        event = _make_event(
            calendar_location=None,
            user_location=None,
        )
        assert event.effective_location is None

    def test_user_location_empty_string_falls_through(self):
        event = _make_event(
            calendar_location="Office",
            user_location="",
        )
        # Empty string is falsy, so calendar_location should be returned
        assert event.effective_location == "Office"


@pytest.mark.unit
class TestIsVirtual:
    """Tests for is_virtual property."""

    def test_virtual_zoom_link(self):
        event = _make_event(calendar_location="https://zoom.us/j/123456")
        assert event.is_virtual is True

    def test_virtual_google_meet(self):
        event = _make_event(calendar_location="https://meet.google.com/abc-defg-hij")
        assert event.is_virtual is True

    def test_physical_location(self):
        event = _make_event(calendar_location="123 Main St, Singapore")
        assert event.is_virtual is False

    def test_no_location_is_not_virtual(self):
        event = _make_event(calendar_location=None)
        assert event.is_virtual is False


@pytest.mark.unit
class TestNeedsTravelFetch:
    """Tests for needs_travel_fetch property."""

    def test_returns_false_for_all_day_events(self):
        event = _make_event(
            calendar_location="Office",
            is_all_day=True,
        )
        assert event.needs_travel_fetch is False

    def test_returns_true_when_no_travel_info(self):
        event = _make_event(
            calendar_location="123 Main St, Singapore",
            is_all_day=False,
        )
        event.route_confirmed = True
        assert event.travel_info is None
        assert event.needs_travel_fetch is True

    def test_returns_false_when_route_not_confirmed(self):
        event = _make_event(
            calendar_location="123 Main St, Singapore",
            is_all_day=False,
        )
        assert event.route_confirmed is False
        assert event.needs_travel_fetch is False

    def test_returns_false_for_virtual_event(self):
        event = _make_event(
            calendar_location="https://zoom.us/j/123",
            is_all_day=False,
        )
        assert event.needs_travel_fetch is False

    def test_returns_false_when_no_location(self):
        event = _make_event(
            calendar_location=None,
            user_location=None,
            is_all_day=False,
        )
        assert event.needs_travel_fetch is False


@pytest.mark.unit
class TestResetAlerts:
    """Tests for reset_alerts method."""

    def test_clears_all_alert_flags(self):
        event = _make_event()
        event.prepare_alerted = True
        event.leave_alerted = True
        event.flat_alerted = True

        event.reset_alerts()

        assert event.prepare_alerted is False
        assert event.leave_alerted is False
        assert event.flat_alerted is False

    def test_reset_on_already_clear_flags(self):
        event = _make_event()
        event.reset_alerts()

        assert event.prepare_alerted is False
        assert event.leave_alerted is False
        assert event.flat_alerted is False


@pytest.mark.unit
class TestPersistAndRestore:
    """Tests for to_persist_dict and restore_user_data round-trip."""

    def test_round_trip_with_user_location(self):
        from integrations.google_calendar.calendar_event import (
            CalendarEvent,
            GeocodedAddress,
        )

        event = _make_event(
            user_location="My Office",
            calendar_location="Other Place",
        )
        event.geocoded_address = GeocodedAddress(
            formatted_address="My Office, Singapore",
            lat=1.35,
            lng=103.82,
        )

        persisted = event.to_persist_dict()

        # Create a fresh event and restore
        new_event = _make_event(
            event_id=event.event_id,
            calendar_location="Other Place",
        )
        CalendarEvent.restore_user_data(new_event, persisted)

        assert new_event.user_location == "My Office"
        assert new_event.geocoded_address is not None
        assert new_event.geocoded_address.formatted_address == "My Office, Singapore"
        assert new_event.geocoded_address.lat == 1.35
        assert new_event.geocoded_address.lng == 103.82

    def test_round_trip_without_geocoded_address(self):
        from integrations.google_calendar.calendar_event import CalendarEvent

        event = _make_event(user_location="Some Place")
        event.geocoded_address = None

        persisted = event.to_persist_dict()

        new_event = _make_event(event_id=event.event_id)
        CalendarEvent.restore_user_data(new_event, persisted)

        assert new_event.user_location == "Some Place"
        assert new_event.geocoded_address is None

    def test_persist_dict_contains_event_id(self):
        event = _make_event(event_id="my-event-123")
        persisted = event.to_persist_dict()
        assert persisted["event_id"] == "my-event-123"

    def test_persist_dict_contains_all_expected_keys(self):
        event = _make_event()
        persisted = event.to_persist_dict()
        expected_keys = {
            "event_id",
            "user_location",
            "geocoded_lat",
            "geocoded_lng",
            "geocoded_formatted",
            "origin_address",
            "route_confirmed",
            "route_declined",
            "confirmed_origin",
            "confirmed_destination",
            "preferred_travel_mode",
        }
        assert set(persisted.keys()) == expected_keys
