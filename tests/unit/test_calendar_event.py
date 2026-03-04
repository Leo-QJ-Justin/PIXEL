"""Tests for CalendarEvent model (simplified — no travel/routing)."""

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
class TestIsVirtual:
    """Tests for is_virtual property."""

    def test_virtual_zoom_link(self):
        event = _make_event(location="https://zoom.us/j/123456")
        assert event.is_virtual is True

    def test_virtual_google_meet(self):
        event = _make_event(location="https://meet.google.com/abc-defg-hij")
        assert event.is_virtual is True

    def test_virtual_teams(self):
        event = _make_event(location="https://teams.microsoft.com/l/meetup-join/abc")
        assert event.is_virtual is True

    def test_physical_location(self):
        event = _make_event(location="123 Main St, Singapore")
        assert event.is_virtual is False

    def test_no_location_is_not_virtual(self):
        event = _make_event(location=None)
        assert event.is_virtual is False


@pytest.mark.unit
class TestAlertedIntervals:
    """Tests for alerted_intervals tracking."""

    def test_starts_empty(self):
        event = _make_event()
        assert event.alerted_intervals == set()

    def test_can_add_intervals(self):
        event = _make_event()
        event.alerted_intervals.add(30)
        event.alerted_intervals.add(5)
        assert event.alerted_intervals == {30, 5}

    def test_separate_instances_have_independent_sets(self):
        event1 = _make_event(event_id="a")
        event2 = _make_event(event_id="b")
        event1.alerted_intervals.add(30)
        assert event2.alerted_intervals == set()


@pytest.mark.unit
class TestResetAlerts:
    """Tests for reset_alerts method."""

    def test_clears_alerted_intervals(self):
        event = _make_event()
        event.alerted_intervals.add(30)
        event.alerted_intervals.add(5)
        event.alerted_intervals.add(0)

        event.reset_alerts()

        assert event.alerted_intervals == set()

    def test_reset_on_already_clear(self):
        event = _make_event()
        event.reset_alerts()
        assert event.alerted_intervals == set()


@pytest.mark.unit
class TestIsVirtualLocation:
    """Tests for the standalone is_virtual_location function."""

    def test_empty_string_is_not_virtual(self):
        from integrations.google_calendar.calendar_event import is_virtual_location

        assert is_virtual_location("") is False

    def test_http_url_is_virtual(self):
        from integrations.google_calendar.calendar_event import is_virtual_location

        assert is_virtual_location("http://example.com/meeting") is True

    def test_webex_is_virtual(self):
        from integrations.google_calendar.calendar_event import is_virtual_location

        assert is_virtual_location("https://webex.com/meet/abc") is True

    def test_plain_text_is_not_virtual(self):
        from integrations.google_calendar.calendar_event import is_virtual_location

        assert is_virtual_location("Conference Room B") is False
