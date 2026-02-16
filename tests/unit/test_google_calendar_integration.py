"""Tests for GoogleCalendarIntegration (refactored with two-phase alerts)."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from integrations.google_calendar.calendar_event import CalendarEvent


def _make_integration(tmp_path, settings=None):
    """Helper to create a GoogleCalendarIntegration instance."""
    from integrations.google_calendar.integration import GoogleCalendarIntegration

    integration_path = tmp_path / "google_calendar"
    integration_path.mkdir(exist_ok=True)

    # Patch event cache loading so it doesn't look for real files
    with patch.object(GoogleCalendarIntegration, "_load_event_cache"):
        return GoogleCalendarIntegration(integration_path, settings or {})


def _make_event(event_id, summary, start_dt, location=""):
    """Build a minimal Google Calendar event dict."""
    return {
        "id": event_id,
        "summary": summary,
        "location": location,
        "start": {"dateTime": start_dt.isoformat()},
    }


@pytest.mark.unit
class TestGoogleCalendarInit:
    """Tests for GoogleCalendarIntegration initialization."""

    def test_initialization(self, tmp_path):
        integration = _make_integration(tmp_path, {"enabled": False})
        assert integration._timer is None
        assert integration._service is None
        assert integration._events == {}
        assert integration._running is False
        assert integration.enabled is False

    def test_name(self, tmp_path):
        integration = _make_integration(tmp_path)
        assert integration.name == "google_calendar"

    def test_display_name(self, tmp_path):
        integration = _make_integration(tmp_path)
        assert integration.display_name == "Google Calendar Alerts"

    def test_default_settings(self, tmp_path):
        integration = _make_integration(tmp_path)
        defaults = integration.get_default_settings()
        assert defaults["enabled"] is False
        assert defaults["check_interval_ms"] == 300000
        assert defaults["alert_before_minutes"] == 30
        assert defaults["trigger_behavior"] == "alert"
        assert defaults["calendar_id"] == "primary"
        assert defaults["origin_address"] == ""
        assert defaults["preparation_minutes"] == 15
        assert defaults["travel_modes"] == ["DRIVE", "TRANSIT"]
        assert defaults["fetch_window_minutes"] == 120
        assert defaults["api_quota_limit"] == 9500


@pytest.mark.unit
class TestParseEventTime:
    """Tests for _parse_event_time."""

    def test_datetime_with_timezone(self, tmp_path):
        from integrations.google_calendar.integration import GoogleCalendarIntegration

        result = GoogleCalendarIntegration._parse_event_time(
            {"dateTime": "2025-01-15T10:00:00+00:00"}
        )
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.tzinfo is not None

    def test_datetime_with_offset(self, tmp_path):
        from integrations.google_calendar.integration import GoogleCalendarIntegration

        result = GoogleCalendarIntegration._parse_event_time(
            {"dateTime": "2025-01-15T10:00:00-05:00"}
        )
        assert result is not None
        assert result.hour == 10

    def test_date_only(self, tmp_path):
        from integrations.google_calendar.integration import GoogleCalendarIntegration

        result = GoogleCalendarIntegration._parse_event_time({"date": "2025-01-15"})
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0
        assert result.tzinfo == timezone.utc

    def test_invalid_datetime(self, tmp_path):
        from integrations.google_calendar.integration import GoogleCalendarIntegration

        result = GoogleCalendarIntegration._parse_event_time({"dateTime": "not-a-date"})
        assert result is None

    def test_invalid_date(self, tmp_path):
        from integrations.google_calendar.integration import GoogleCalendarIntegration

        result = GoogleCalendarIntegration._parse_event_time({"date": "not-a-date"})
        assert result is None

    def test_empty_dict(self, tmp_path):
        from integrations.google_calendar.integration import GoogleCalendarIntegration

        result = GoogleCalendarIntegration._parse_event_time({})
        assert result is None


@pytest.mark.unit
class TestProcessEvents:
    """Tests for _process_events (async, two-phase alerts)."""

    @pytest.mark.asyncio
    async def test_flat_alert_within_threshold(self, tmp_path):
        """Event within alert_before_minutes triggers flat alert."""
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        event = _make_event("evt1", "Team Meeting", now + timedelta(minutes=15), "Office")

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        with patch.object(integration, "_has_routing_provider", return_value=False):
            await integration._process_events([event], now)

        assert len(received) == 1
        assert received[0][0] == "alert"
        assert received[0][1]["source"] == "google_calendar"
        assert received[0][1]["summary"] == "Team Meeting"

    @pytest.mark.asyncio
    async def test_event_outside_threshold_no_alert(self, tmp_path):
        """Event outside alert_before_minutes does not trigger alert."""
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        event = _make_event("evt1", "Future Meeting", now + timedelta(minutes=45))

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        await integration._process_events([event], now)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_already_alerted_event_not_retriggered(self, tmp_path):
        """Flat alert should not re-trigger for the same event."""
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        event = _make_event("evt1", "Team Meeting", now + timedelta(minutes=15))

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        await integration._process_events([event], now)
        await integration._process_events([event], now)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_past_event_not_alerted(self, tmp_path):
        """Events that have already started should not trigger alerts."""
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        event = _make_event("evt1", "Past Meeting", now - timedelta(minutes=5))

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        await integration._process_events([event], now)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_multiple_events_trigger_separately(self, tmp_path):
        """Multiple events within threshold each trigger their own alert."""
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        events = [
            _make_event("evt1", "Meeting 1", now + timedelta(minutes=10), "Room A"),
            _make_event("evt2", "Meeting 2", now + timedelta(minutes=20), "Room B"),
        ]

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        with patch.object(integration, "_has_routing_provider", return_value=False):
            await integration._process_events(events, now)

        assert len(received) == 2
        summaries = {r[1]["summary"] for r in received}
        assert summaries == {"Meeting 1", "Meeting 2"}

    @pytest.mark.asyncio
    async def test_all_day_event_uses_flat_alert(self, tmp_path):
        """All-day events skip travel time and use flat alert."""
        integration = _make_integration(
            tmp_path,
            {"alert_before_minutes": 30, "origin_address": "Home"},
        )
        now = datetime.now(timezone.utc)
        # All-day event uses 'date' instead of 'dateTime'
        event = {
            "id": "allday1",
            "summary": "Company Holiday",
            "location": "Office",
            "start": {"date": (now + timedelta(minutes=15)).strftime("%Y-%m-%d")},
        }

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        # All-day events have time set to midnight UTC, so this only fires
        # if the event start is within alert_before_minutes
        await integration._process_events([event], now)

        # The event should be tracked as all-day
        cal_event = integration._events.get("allday1")
        assert cal_event is not None
        assert cal_event.is_all_day is True


@pytest.mark.unit
class TestTriggerFlatAlert:
    """Tests for _trigger_flat_alert."""

    def test_context_keys(self, tmp_path):
        integration = _make_integration(tmp_path, {"trigger_behavior": "alert"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        event = CalendarEvent(
            event_id="evt123",
            summary="Standup",
            start_time=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
            is_all_day=False,
            calendar_location="Room 42",
        )
        integration._trigger_flat_alert(event, 15.3)

        assert len(received) == 1
        name, ctx = received[0]
        assert name == "alert"
        assert ctx["source"] == "google_calendar"
        assert ctx["event_id"] == "evt123"
        assert ctx["summary"] == "Standup"
        assert ctx["location"] == "Room 42"
        assert ctx["minutes_until"] == 15.3

    def test_bubble_text_format(self, tmp_path):
        integration = _make_integration(tmp_path, {"trigger_behavior": "alert"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        event = CalendarEvent(
            event_id="evt1",
            summary="Lunch",
            start_time=datetime(2025, 1, 15, 12, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )
        integration._trigger_flat_alert(event, 10.4)

        assert received[0][1]["bubble_text"] == "Lunch in 10 min"

    def test_custom_trigger_behavior(self, tmp_path):
        integration = _make_integration(tmp_path, {"trigger_behavior": "wave"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        event = CalendarEvent(
            event_id="evt1",
            summary="Test",
            start_time=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )
        integration._trigger_flat_alert(event, 5.0)

        assert received[0][0] == "wave"


@pytest.mark.unit
class TestUpsertEvent:
    """Tests for _upsert_event."""

    def test_creates_new_event(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)
        raw = _make_event("evt1", "New Meeting", now + timedelta(minutes=30), "Office")

        event = integration._upsert_event(raw)

        assert event is not None
        assert event.event_id == "evt1"
        assert event.summary == "New Meeting"
        assert event.calendar_location == "Office"
        assert "evt1" in integration._events

    def test_updates_existing_event(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)
        raw = _make_event("evt1", "Meeting", now + timedelta(minutes=30))

        integration._upsert_event(raw)

        raw_updated = _make_event("evt1", "Updated Meeting", now + timedelta(minutes=30))
        event = integration._upsert_event(raw_updated)

        assert event.summary == "Updated Meeting"
        assert len(integration._events) == 1

    def test_resets_alerts_on_time_change(self, tmp_path):
        """Edge case #11: changing start_time resets alert state."""
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)
        raw = _make_event("evt1", "Meeting", now + timedelta(minutes=30))

        event = integration._upsert_event(raw)
        event.flat_alerted = True
        event.prepare_alerted = True

        # Update with different time
        raw_updated = _make_event("evt1", "Meeting", now + timedelta(minutes=60))
        event = integration._upsert_event(raw_updated)

        assert event.flat_alerted is False
        assert event.prepare_alerted is False

    def test_returns_none_for_invalid_event(self, tmp_path):
        integration = _make_integration(tmp_path)
        assert integration._upsert_event({}) is None
        assert integration._upsert_event({"id": ""}) is None
        assert integration._upsert_event({"id": "x", "start": {}}) is None


@pytest.mark.unit
class TestCleanupEvents:
    """Tests for _cleanup_events."""

    def test_removes_stale_events(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        # Add events to internal state
        for eid in ["evt1", "evt2", "evt3"]:
            integration._events[eid] = CalendarEvent(
                event_id=eid,
                summary=f"Event {eid}",
                start_time=now + timedelta(minutes=30),
                is_all_day=False,
            )

        current_events = [{"id": "evt2"}, {"id": "evt4"}]
        integration._cleanup_events(current_events)

        assert set(integration._events.keys()) == {"evt2"}

    def test_keeps_current_events(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        for eid in ["evt1", "evt2"]:
            integration._events[eid] = CalendarEvent(
                event_id=eid,
                summary=f"Event {eid}",
                start_time=now + timedelta(minutes=30),
                is_all_day=False,
            )

        current_events = [{"id": "evt1"}, {"id": "evt2"}]
        integration._cleanup_events(current_events)

        assert set(integration._events.keys()) == {"evt1", "evt2"}

    def test_empty_events_clears_all(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        for eid in ["evt1", "evt2"]:
            integration._events[eid] = CalendarEvent(
                event_id=eid,
                summary=f"Event {eid}",
                start_time=now + timedelta(minutes=30),
                is_all_day=False,
            )

        integration._cleanup_events([])

        assert integration._events == {}


@pytest.mark.unit
class TestStartWithoutCredentials:
    """Tests for start method without credentials."""

    @pytest.mark.asyncio
    async def test_start_without_credentials_logs_error(self, tmp_path, caplog):
        integration = _make_integration(tmp_path)

        with patch(
            "integrations.google_calendar.integration.load_credentials",
            return_value=None,
        ):
            await integration.start()

        assert "credentials not available" in caplog.text
        assert integration._timer is None
        assert integration._running is False


@pytest.mark.unit
class TestStop:
    """Tests for stop method."""

    @pytest.mark.asyncio
    async def test_stop_clears_state(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        integration._events["evt1"] = CalendarEvent(
            event_id="evt1",
            summary="Test",
            start_time=now + timedelta(minutes=30),
            is_all_day=False,
        )

        with patch.object(integration, "_save_event_cache"):
            await integration.stop()

        assert integration._timer is None
        assert integration._running is False
        assert integration._service is None
        assert integration._events == {}


@pytest.mark.unit
class TestNotifyPrepare:
    """Tests for _notify_prepare (Phase 1: bubble only)."""

    def test_emits_notification_signal(self, tmp_path):
        integration = _make_integration(tmp_path)

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        event = CalendarEvent(
            event_id="evt1",
            summary="Standup",
            start_time=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )
        integration._notify_prepare(event, 10)

        assert len(received) == 1
        assert received[0]["action"] == "prepare"
        assert "Get ready" in received[0]["bubble_text"]
        assert "leave in 10 min" in received[0]["bubble_text"]

    def test_does_not_trigger_behavior(self, tmp_path):
        """Prepare phase should NOT trigger behavior system (edge case #1)."""
        integration = _make_integration(tmp_path)

        behavior_received = []
        integration.request_behavior.connect(
            lambda name, ctx: behavior_received.append((name, ctx))
        )

        event = CalendarEvent(
            event_id="evt1",
            summary="Meeting",
            start_time=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )
        integration._notify_prepare(event, 5)

        assert len(behavior_received) == 0


@pytest.mark.unit
class TestTriggerLeaveAlert:
    """Tests for _trigger_leave_alert (Phase 2: full alert)."""

    def test_triggers_alert_behavior(self, tmp_path):
        integration = _make_integration(tmp_path, {"trigger_behavior": "alert"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        event = CalendarEvent(
            event_id="evt1",
            summary="Client Meeting",
            start_time=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
            is_all_day=False,
            calendar_location="Downtown Office",
        )
        integration._trigger_leave_alert(event, 25, "DRIVE")

        assert len(received) == 1
        name, ctx = received[0]
        assert name == "alert"
        assert ctx["source"] == "google_calendar"
        assert ctx["travel_minutes"] == 25
        assert ctx["travel_mode"] == "DRIVE"
        assert "Time to go" in ctx["bubble_text"]


@pytest.mark.unit
class TestDefaultSettings:
    """Tests for new default settings."""

    def test_new_settings_present(self, tmp_path):
        integration = _make_integration(tmp_path)
        defaults = integration.get_default_settings()
        assert defaults["recheck_offset_minutes"] == 20
        assert defaults["leave_buffer_minutes"] == 5
        assert defaults["tap_refresh_debounce_ms"] == 5000


@pytest.mark.unit
class TestTwoFetchModel:
    """Tests for the two-fetch model (initial fetch + scheduled recheck)."""

    @pytest.mark.asyncio
    async def test_initial_fetch_sets_flag_and_schedules_recheck(self, tmp_path):
        """Route-confirmed event triggers initial fetch and schedules recheck."""
        from integrations.google_calendar.calendar_event import TravelEstimate, TravelInfo

        integration = _make_integration(tmp_path, {"preparation_minutes": 15})
        now = datetime.now(timezone.utc)
        event_time = now + timedelta(minutes=90)
        raw = _make_event("evt1", "Meeting", event_time, "Office")

        # Upsert and manually confirm route
        event = integration._upsert_event(raw)
        event.route_confirmed = True
        event.origin_address = "Home"

        # Mock _fetch_travel_info to populate travel_info
        async def mock_fetch(ev, origin):
            ev.travel_info = TravelInfo(
                location="Office",
                estimates=[TravelEstimate(mode="DRIVE", duration_minutes=25)],
                fetched_at=now,
            )

        with patch.object(integration, "_fetch_travel_info", side_effect=mock_fetch):
            with patch.object(integration, "_has_routing_provider", return_value=True):
                await integration._process_events([raw], now)

        assert event.initial_fetch_done is True
        # Recheck timer should be scheduled
        assert event.event_id in integration._recheck_timers

        # Clean up timer
        integration._cancel_recheck_timer(event.event_id)

    @pytest.mark.asyncio
    async def test_no_refetch_after_initial_fetch_done(self, tmp_path):
        """Once initial_fetch_done is True, no automatic re-fetch via poll."""
        from integrations.google_calendar.calendar_event import TravelEstimate, TravelInfo

        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)
        event_time = now + timedelta(minutes=90)
        raw = _make_event("evt1", "Meeting", event_time, "Office")

        event = integration._upsert_event(raw)
        event.route_confirmed = True
        event.origin_address = "Home"
        event.initial_fetch_done = True
        event.travel_info = TravelInfo(
            location="Office",
            estimates=[TravelEstimate(mode="DRIVE", duration_minutes=25)],
            fetched_at=now,
        )

        fetch_called = False

        async def mock_fetch(ev, origin):
            nonlocal fetch_called
            fetch_called = True

        with patch.object(integration, "_fetch_travel_info", side_effect=mock_fetch):
            with patch.object(integration, "_has_routing_provider", return_value=True):
                await integration._process_events([raw], now)

        assert fetch_called is False

    @pytest.mark.asyncio
    async def test_recheck_sets_done_flag(self, tmp_path):
        """Executing recheck sets recheck_done=True."""
        from integrations.google_calendar.calendar_event import TravelEstimate, TravelInfo

        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Meeting",
            start_time=now + timedelta(minutes=60),
            is_all_day=False,
            calendar_location="Office",
        )
        event.route_confirmed = True
        event.origin_address = "Home"
        event.initial_fetch_done = True
        event.travel_info = TravelInfo(
            location="Office",
            estimates=[TravelEstimate(mode="DRIVE", duration_minutes=25)],
            fetched_at=now,
        )
        integration._events["evt1"] = event

        async def mock_fetch(ev, origin):
            ev.travel_info = TravelInfo(
                location="Office",
                estimates=[TravelEstimate(mode="DRIVE", duration_minutes=28)],
                fetched_at=now,
            )

        with patch.object(integration, "_fetch_travel_info", side_effect=mock_fetch):
            with patch.object(integration, "_save_event_cache"):
                await integration._execute_recheck("evt1")

        assert event.recheck_done is True


@pytest.mark.unit
class TestTapRefresh:
    """Tests for tap-to-refresh functionality."""

    def test_finds_most_imminent_event(self, tmp_path):
        """_find_most_imminent_event returns the event with nearest departure."""
        from integrations.google_calendar.calendar_event import TravelEstimate, TravelInfo

        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        # Event A: departs in 30 min (start in 60, travel 30)
        event_a = CalendarEvent(
            event_id="a",
            summary="Event A",
            start_time=now + timedelta(minutes=60),
            is_all_day=False,
            calendar_location="Place A",
        )
        event_a.route_confirmed = True
        event_a.travel_info = TravelInfo(
            location="Place A",
            estimates=[TravelEstimate(mode="DRIVE", duration_minutes=30)],
            fetched_at=now,
        )

        # Event B: departs in 50 min (start in 90, travel 40)
        event_b = CalendarEvent(
            event_id="b",
            summary="Event B",
            start_time=now + timedelta(minutes=90),
            is_all_day=False,
            calendar_location="Place B",
        )
        event_b.route_confirmed = True
        event_b.travel_info = TravelInfo(
            location="Place B",
            estimates=[TravelEstimate(mode="DRIVE", duration_minutes=40)],
            fetched_at=now,
        )

        integration._events = {"a": event_a, "b": event_b}

        result = integration._find_most_imminent_event()
        assert result is not None
        assert result.event_id == "a"

    def test_returns_none_when_no_eligible_events(self, tmp_path):
        """Returns None when no events have confirmed routes."""
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Meeting",
            start_time=now + timedelta(minutes=60),
            is_all_day=False,
        )
        integration._events = {"evt1": event}

        assert integration._find_most_imminent_event() is None

    def test_debounce_prevents_rapid_calls(self, tmp_path):
        """Tap-to-refresh is debounced."""
        from integrations.google_calendar.calendar_event import TravelEstimate, TravelInfo

        integration = _make_integration(tmp_path, {"tap_refresh_debounce_ms": 5000})
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Meeting",
            start_time=now + timedelta(minutes=60),
            is_all_day=False,
            calendar_location="Office",
        )
        event.route_confirmed = True
        event.origin_address = "Home"
        event.travel_info = TravelInfo(
            location="Office",
            estimates=[TravelEstimate(mode="DRIVE", duration_minutes=25)],
            fetched_at=now,
        )
        integration._events = {"evt1": event}

        # First call sets debounce timestamp
        integration._last_tap_refresh_time = now

        # Immediate second call should be debounced
        with patch.object(integration, "_find_most_imminent_event") as mock_find:
            integration.tap_refresh()
            mock_find.assert_not_called()


@pytest.mark.unit
class TestCleanupEventsTimers:
    """Tests for timer cleanup during event removal."""

    def test_cancels_recheck_timer_on_cleanup(self, tmp_path):
        """Recheck timer is cancelled when event is removed."""
        from PyQt6.QtCore import QTimer

        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        integration._events["evt1"] = CalendarEvent(
            event_id="evt1",
            summary="Event",
            start_time=now + timedelta(minutes=30),
            is_all_day=False,
        )
        timer = QTimer()
        integration._recheck_timers["evt1"] = timer

        integration._cleanup_events([])

        assert "evt1" not in integration._events
        assert "evt1" not in integration._recheck_timers


@pytest.mark.unit
class TestSmarterOrigin:
    """Tests for smarter origin suggestion (last destination as next origin)."""

    def test_confirm_route_stores_destination(self, tmp_path):
        """confirm_route stores the confirmed destination for next event."""
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Meeting",
            start_time=now + timedelta(minutes=60),
            is_all_day=False,
            calendar_location="Office",
        )
        event.confirmed_destination = "123 Main St, Singapore"
        event.origin_address = "Home"
        integration._events["evt1"] = event

        with patch.object(integration, "_save_event_cache"):
            integration.confirm_route("evt1")

        assert integration._last_confirmed_destination == "123 Main St, Singapore"
