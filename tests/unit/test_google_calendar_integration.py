"""Tests for GoogleCalendarIntegration (simplified — reminders + day preview)."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from integrations.google_calendar.calendar_event import CalendarEvent


def _make_integration(tmp_path, settings=None):
    """Helper to create a GoogleCalendarIntegration instance."""
    from integrations.google_calendar.integration import GoogleCalendarIntegration

    integration_path = tmp_path / "google_calendar"
    integration_path.mkdir(exist_ok=True)

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
        assert integration.display_name == "Google Calendar"

    def test_default_settings(self, tmp_path):
        integration = _make_integration(tmp_path)
        defaults = integration.get_default_settings()
        assert defaults["enabled"] is False
        assert defaults["check_interval_ms"] == 300_000
        assert defaults["trigger_behavior"] == "alert"
        assert defaults["calendar_id"] == "primary"
        assert defaults["fetch_window_minutes"] == 120
        assert defaults["reminder_minutes"] == [30, 5, 0]
        assert defaults["day_preview_enabled"] is True


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
        assert event.location == "Office"
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
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)
        raw = _make_event("evt1", "Meeting", now + timedelta(minutes=30))

        event = integration._upsert_event(raw)
        event.alerted_intervals.add(30)
        event.alerted_intervals.add(5)

        # Update with different time
        raw_updated = _make_event("evt1", "Meeting", now + timedelta(minutes=60))
        event = integration._upsert_event(raw_updated)

        assert event.alerted_intervals == set()

    def test_returns_none_for_invalid_event(self, tmp_path):
        integration = _make_integration(tmp_path)
        assert integration._upsert_event({}) is None
        assert integration._upsert_event({"id": ""}) is None
        assert integration._upsert_event({"id": "x", "start": {}}) is None

    def test_all_day_event_detection(self, tmp_path):
        integration = _make_integration(tmp_path)
        raw = {
            "id": "allday1",
            "summary": "Holiday",
            "start": {"date": "2025-06-15"},
        }
        event = integration._upsert_event(raw)
        assert event is not None
        assert event.is_all_day is True


@pytest.mark.unit
class TestProcessReminders:
    """Tests for _process_reminders."""

    def test_fires_30_min_reminder(self, tmp_path):
        integration = _make_integration(tmp_path, {"reminder_minutes": [30, 5, 0]})
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Team Meeting",
            start_time=now + timedelta(minutes=25),
            is_all_day=False,
        )

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._process_reminders(event, now)

        assert len(received) == 1
        assert "Team Meeting in 30 min" in received[0]["bubble_text"]
        assert 30 in event.alerted_intervals

    def test_fires_5_min_reminder_with_exclamation(self, tmp_path):
        integration = _make_integration(tmp_path, {"reminder_minutes": [30, 5, 0]})
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Standup",
            start_time=now + timedelta(minutes=3),
            is_all_day=False,
        )
        event.alerted_intervals.add(30)  # Already fired 30-min

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._process_reminders(event, now)

        assert len(received) == 1
        assert "Standup in 5 min!" in received[0]["bubble_text"]
        assert 5 in event.alerted_intervals

    def test_fires_starting_now_with_behavior(self, tmp_path):
        integration = _make_integration(
            tmp_path, {"reminder_minutes": [30, 5, 0], "trigger_behavior": "alert"}
        )
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Design Review",
            start_time=now,  # exactly now
            is_all_day=False,
        )
        # Can't use start_time == now because that's <= check; use a tiny future offset
        event.start_time = now + timedelta(seconds=1)
        event.alerted_intervals = {30, 5}

        behavior_received = []
        integration.request_behavior.connect(
            lambda name, ctx: behavior_received.append((name, ctx))
        )

        integration._process_reminders(event, now)

        assert len(behavior_received) == 1
        assert behavior_received[0][0] == "alert"
        assert "starting now!" in behavior_received[0][1]["bubble_text"]
        assert 0 in event.alerted_intervals

    def test_skips_all_day_events(self, tmp_path):
        integration = _make_integration(tmp_path, {"reminder_minutes": [30, 5, 0]})
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="allday1",
            summary="Holiday",
            start_time=now + timedelta(minutes=10),
            is_all_day=True,
        )

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))
        behavior_received = []
        integration.request_behavior.connect(
            lambda name, ctx: behavior_received.append((name, ctx))
        )

        integration._process_reminders(event, now)

        assert len(received) == 0
        assert len(behavior_received) == 0

    def test_skips_past_events(self, tmp_path):
        integration = _make_integration(tmp_path, {"reminder_minutes": [30, 5, 0]})
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Past Meeting",
            start_time=now - timedelta(minutes=5),
            is_all_day=False,
        )

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._process_reminders(event, now)

        assert len(received) == 0

    def test_no_duplicate_alerts(self, tmp_path):
        integration = _make_integration(tmp_path, {"reminder_minutes": [30, 5, 0]})
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Meeting",
            start_time=now + timedelta(minutes=20),
            is_all_day=False,
        )

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._process_reminders(event, now)
        integration._process_reminders(event, now)

        # Should only fire once for the 30-min interval
        assert len(received) == 1

    def test_event_outside_all_intervals(self, tmp_path):
        integration = _make_integration(tmp_path, {"reminder_minutes": [30, 5, 0]})
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Far Future Meeting",
            start_time=now + timedelta(minutes=60),
            is_all_day=False,
        )

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._process_reminders(event, now)

        assert len(received) == 0

    def test_multiple_intervals_fire_together(self, tmp_path):
        """If event is within 30 seconds, all intervals fire at once."""
        integration = _make_integration(tmp_path, {"reminder_minutes": [30, 5, 0]})
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            event_id="evt1",
            summary="Urgent",
            start_time=now + timedelta(seconds=30),
            is_all_day=False,
        )

        notifications = []
        integration.request_notification.connect(lambda ctx: notifications.append(ctx))
        behaviors = []
        integration.request_behavior.connect(lambda name, ctx: behaviors.append((name, ctx)))

        integration._process_reminders(event, now)

        # 30-min and 5-min fire as notifications, 0-min fires as behavior
        assert len(notifications) == 2
        assert len(behaviors) == 1
        assert event.alerted_intervals == {30, 5, 0}


@pytest.mark.unit
class TestDayPreview:
    """Tests for _emit_day_preview."""

    def test_no_events_free_day(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._emit_day_preview(now)

        assert len(received) == 1
        assert "free day" in received[0]["bubble_text"]

    def test_one_timed_event(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        integration._events["evt1"] = CalendarEvent(
            event_id="evt1",
            summary="Standup",
            start_time=now.replace(hour=9, minute=30, second=0, microsecond=0),
            is_all_day=False,
        )

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._emit_day_preview(now)

        assert len(received) == 1
        assert "1 meeting today" in received[0]["bubble_text"]
        assert "Standup" in received[0]["bubble_text"]

    def test_multiple_timed_events(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        for i, (name, hour) in enumerate([("Standup", 9), ("Design Review", 11), ("Retro", 15)]):
            integration._events[f"evt{i}"] = CalendarEvent(
                event_id=f"evt{i}",
                summary=name,
                start_time=now.replace(hour=hour, minute=0, second=0, microsecond=0),
                is_all_day=False,
            )

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._emit_day_preview(now)

        assert len(received) == 1
        assert "3 meetings today" in received[0]["bubble_text"]
        assert "Standup" in received[0]["bubble_text"]  # First event

    def test_only_all_day_events(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        integration._events["allday1"] = CalendarEvent(
            event_id="allday1",
            summary="Alice's Birthday",
            start_time=now.replace(hour=0, minute=0, second=0, microsecond=0),
            is_all_day=True,
        )

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._emit_day_preview(now)

        assert len(received) == 1
        assert "all-day event" in received[0]["bubble_text"]
        assert "Alice's Birthday" in received[0]["bubble_text"]

    def test_bubble_duration_set(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        received = []
        integration.request_notification.connect(lambda ctx: received.append(ctx))

        integration._emit_day_preview(now)

        assert received[0]["bubble_duration_ms"] == 8000


@pytest.mark.unit
class TestCleanupEvents:
    """Tests for _cleanup_events."""

    def test_removes_stale_events(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

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
class TestGetNextEvent:
    """Tests for get_next_event."""

    def test_returns_nearest_event(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        integration._events["evt1"] = CalendarEvent(
            event_id="evt1",
            summary="Later",
            start_time=now + timedelta(minutes=60),
            is_all_day=False,
        )
        integration._events["evt2"] = CalendarEvent(
            event_id="evt2",
            summary="Sooner",
            start_time=now + timedelta(minutes=10),
            is_all_day=False,
        )

        result = integration.get_next_event()
        assert result is not None
        assert result.event_id == "evt2"

    def test_returns_none_when_empty(self, tmp_path):
        integration = _make_integration(tmp_path)
        assert integration.get_next_event() is None

    def test_skips_all_day_events(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        integration._events["allday1"] = CalendarEvent(
            event_id="allday1",
            summary="Holiday",
            start_time=now + timedelta(minutes=10),
            is_all_day=True,
        )

        assert integration.get_next_event() is None

    def test_skips_past_events(self, tmp_path):
        integration = _make_integration(tmp_path)
        now = datetime.now(timezone.utc)

        integration._events["evt1"] = CalendarEvent(
            event_id="evt1",
            summary="Past",
            start_time=now - timedelta(minutes=5),
            is_all_day=False,
        )

        assert integration.get_next_event() is None


@pytest.mark.unit
class TestStartWithoutCredentials:
    """Tests for start method without credentials."""

    @pytest.mark.asyncio
    async def test_start_without_credentials_stays_dormant(self, tmp_path, caplog):
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

        await integration.stop()

        assert integration._timer is None
        assert integration._running is False
        assert integration._service is None
        assert integration._events == {}
