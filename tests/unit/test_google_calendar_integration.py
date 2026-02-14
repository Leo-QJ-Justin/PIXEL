"""Tests for GoogleCalendarIntegration."""

from datetime import datetime, timedelta, timezone

import pytest


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
        assert integration._alerted_event_ids == set()
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
    """Tests for _process_events."""

    def test_event_within_threshold_triggers_alert(self, tmp_path):
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        event = _make_event("evt1", "Team Meeting", now + timedelta(minutes=15))

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration._process_events([event], now)

        assert len(received) == 1
        assert received[0][0] == "alert"
        assert received[0][1]["source"] == "google_calendar"
        assert received[0][1]["summary"] == "Team Meeting"

    def test_event_outside_threshold_no_alert(self, tmp_path):
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        event = _make_event("evt1", "Future Meeting", now + timedelta(minutes=45))

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration._process_events([event], now)

        assert len(received) == 0

    def test_already_alerted_event_not_retriggered(self, tmp_path):
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        event = _make_event("evt1", "Team Meeting", now + timedelta(minutes=15))

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration._process_events([event], now)
        integration._process_events([event], now)

        assert len(received) == 1

    def test_past_event_not_alerted(self, tmp_path):
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        event = _make_event("evt1", "Past Meeting", now - timedelta(minutes=5))

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration._process_events([event], now)

        assert len(received) == 0

    def test_multiple_events_trigger_separately(self, tmp_path):
        integration = _make_integration(tmp_path, {"alert_before_minutes": 30})
        now = datetime.now(timezone.utc)
        events = [
            _make_event("evt1", "Meeting 1", now + timedelta(minutes=10)),
            _make_event("evt2", "Meeting 2", now + timedelta(minutes=20)),
        ]

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration._process_events(events, now)

        assert len(received) == 2
        summaries = {r[1]["summary"] for r in received}
        assert summaries == {"Meeting 1", "Meeting 2"}


@pytest.mark.unit
class TestTriggerEventAlert:
    """Tests for _trigger_event_alert."""

    def test_context_keys(self, tmp_path):
        integration = _make_integration(tmp_path, {"trigger_behavior": "alert"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        event = {
            "id": "evt123",
            "summary": "Standup",
            "location": "Room 42",
            "start": {"dateTime": "2025-01-15T10:00:00+00:00"},
        }
        integration._trigger_event_alert(event, 15.3)

        assert len(received) == 1
        name, ctx = received[0]
        assert name == "alert"
        assert ctx["source"] == "google_calendar"
        assert ctx["event_id"] == "evt123"
        assert ctx["summary"] == "Standup"
        assert ctx["location"] == "Room 42"
        assert ctx["start_time"] == "2025-01-15T10:00:00+00:00"
        assert ctx["minutes_until"] == 15.3

    def test_bubble_text_format(self, tmp_path):
        integration = _make_integration(tmp_path, {"trigger_behavior": "alert"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        event = {
            "id": "evt1",
            "summary": "Lunch",
            "location": "",
            "start": {"dateTime": "2025-01-15T12:00:00+00:00"},
        }
        integration._trigger_event_alert(event, 10.4)

        assert received[0][1]["bubble_text"] == "Lunch in 10 min"

    def test_custom_trigger_behavior(self, tmp_path):
        integration = _make_integration(tmp_path, {"trigger_behavior": "wave"})

        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        event = {
            "id": "evt1",
            "summary": "Test",
            "location": "",
            "start": {"dateTime": "2025-01-15T10:00:00+00:00"},
        }
        integration._trigger_event_alert(event, 5.0)

        assert received[0][0] == "wave"


@pytest.mark.unit
class TestCleanupAlertedIds:
    """Tests for _cleanup_alerted_ids."""

    def test_removes_stale_ids(self, tmp_path):
        integration = _make_integration(tmp_path)
        integration._alerted_event_ids = {"evt1", "evt2", "evt3"}

        current_events = [{"id": "evt2"}, {"id": "evt4"}]
        integration._cleanup_alerted_ids(current_events)

        assert integration._alerted_event_ids == {"evt2"}

    def test_keeps_current_ids(self, tmp_path):
        integration = _make_integration(tmp_path)
        integration._alerted_event_ids = {"evt1", "evt2"}

        current_events = [{"id": "evt1"}, {"id": "evt2"}]
        integration._cleanup_alerted_ids(current_events)

        assert integration._alerted_event_ids == {"evt1", "evt2"}

    def test_empty_events_clears_all(self, tmp_path):
        integration = _make_integration(tmp_path)
        integration._alerted_event_ids = {"evt1", "evt2"}

        integration._cleanup_alerted_ids([])

        assert integration._alerted_event_ids == set()


@pytest.mark.unit
class TestStartWithoutCredentials:
    """Tests for start method without credentials."""

    @pytest.mark.asyncio
    async def test_start_without_credentials_logs_error(self, tmp_path, caplog, monkeypatch):
        monkeypatch.delenv("GOOGLE_CALENDAR_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CALENDAR_CLIENT_SECRET", raising=False)

        integration = _make_integration(tmp_path)
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
        integration._alerted_event_ids = {"evt1", "evt2"}
        await integration.stop()

        assert integration._timer is None
        assert integration._running is False
        assert integration._service is None
        assert integration._alerted_event_ids == set()
