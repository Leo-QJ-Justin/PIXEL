"""Tests for bridge_journal event wiring."""

import json
from unittest.mock import MagicMock

import pytest

from src.ui.bridge import BridgeHost
from src.ui.bridge_journal import wire_journal_events


def _make_bridge_and_capture():
    """Create a BridgeHost with a JS callback that captures emitted events."""
    bridge = BridgeHost()
    emitted: list[tuple[str, object]] = []

    def _capture(event: str, payload_json: str):
        emitted.append((event, json.loads(payload_json)))

    bridge.register_js_callback(_capture)
    return bridge, emitted


def _make_mock_integration(store):
    """Build a mock JournalIntegration that returns the given store."""
    integration = MagicMock()
    integration._get_store.return_value = store
    integration.get_daily_prompt.return_value = "How was your day?"
    return integration


@pytest.mark.unit
class TestLoadStats:
    """journal.loadStats triggers stats emission with correct fields."""

    def test_emits_stats_and_daily_prompt(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        store.get_streak.return_value = (5, 10)
        store.get_total_count.return_value = 42
        store.get_mood_trend.return_value = [
            {"date": "2025-01-01", "mood": "happy"},
        ]
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        bridge.receive("journal.loadStats", json.dumps({}))

        # Should emit journal.stats and journal.dailyPrompt
        events = {e[0]: e[1] for e in emitted}
        assert "journal.stats" in events
        stats = events["journal.stats"]
        assert stats["currentStreak"] == 5
        assert stats["bestStreak"] == 10
        assert stats["totalCount"] == 42
        assert stats["moodTrend"] == [{"date": "2025-01-01", "mood": "happy"}]

        assert "journal.dailyPrompt" in events
        assert events["journal.dailyPrompt"]["prompt"] == "How was your day?"

    def test_emits_empty_on_error(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        store.get_streak.side_effect = RuntimeError("db locked")
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        bridge.receive("journal.loadStats", json.dumps({}))

        events = {e[0]: e[1] for e in emitted}
        assert events.get("journal.stats") == {}


@pytest.mark.unit
class TestSave:
    """journal.save calls store.save_entry with correct args and emits saved."""

    def test_save_entry_and_emit(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        store.save_entry.return_value = 7
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        payload = {
            "date": "2025-06-15",
            "mode": "freeform",
            "mood": "happy",
            "raw_text": "Great day!",
            "clean_text": "Great day!",
            "prompt_used": "How was your day?",
        }
        bridge.receive("journal.save", json.dumps(payload))

        store.save_entry.assert_called_once_with(
            entry_date="2025-06-15",
            mode="freeform",
            mood="happy",
            raw_text="Great day!",
            clean_text="Great day!",
            prompt_used="How was your day?",
        )
        integration.on_entry_saved.assert_called_once_with("happy")

        events = {e[0]: e[1] for e in emitted}
        assert "journal.saved" in events
        assert events["journal.saved"]["id"] == 7
        assert events["journal.saved"]["date"] == "2025-06-15"

    def test_save_with_optional_fields_none(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        store.save_entry.return_value = 1
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        payload = {
            "date": "2025-06-15",
            "mode": "guided",
            "raw_text": "Just a note",
        }
        bridge.receive("journal.save", json.dumps(payload))

        store.save_entry.assert_called_once_with(
            entry_date="2025-06-15",
            mode="guided",
            mood=None,
            raw_text="Just a note",
            clean_text=None,
            prompt_used=None,
        )

    def test_save_error_emits_error(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        store.save_entry.side_effect = RuntimeError("write failed")
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        payload = {
            "date": "2025-06-15",
            "mode": "freeform",
            "raw_text": "text",
        }
        bridge.receive("journal.save", json.dumps(payload))

        events = {e[0]: e[1] for e in emitted}
        assert events["journal.saved"]["error"] is True


@pytest.mark.unit
class TestDelete:
    """journal.delete calls store.delete_entry and emits deleted."""

    def test_delete_entry(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        bridge.receive("journal.delete", json.dumps({"date": "2025-06-15"}))

        store.delete_entry.assert_called_once_with("2025-06-15")

        events = {e[0]: e[1] for e in emitted}
        assert "journal.deleted" in events
        assert events["journal.deleted"]["date"] == "2025-06-15"

    def test_delete_error_emits_error(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        store.delete_entry.side_effect = RuntimeError("db locked")
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        bridge.receive("journal.delete", json.dumps({"date": "2025-06-15"}))

        events = {e[0]: e[1] for e in emitted}
        assert events["journal.deleted"]["error"] is True


@pytest.mark.unit
class TestLoadMonth:
    """journal.loadMonth emits monthData with dates and moods."""

    def test_load_month_data(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        store.get_entries_for_month.return_value = [
            {"date": "2025-06-01", "mood": "happy"},
            {"date": "2025-06-05", "mood": None},
            {"date": "2025-06-10", "mood": "sad"},
        ]
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        bridge.receive("journal.loadMonth", json.dumps({"year": 2025, "month": 6}))

        store.get_entries_for_month.assert_called_once_with(2025, 6)

        events = {e[0]: e[1] for e in emitted}
        assert "journal.monthData" in events
        month_data = events["journal.monthData"]
        assert month_data["dates"] == ["2025-06-01", "2025-06-05", "2025-06-10"]
        assert month_data["moods"] == {"2025-06-01": "happy", "2025-06-10": "sad"}

    def test_load_month_empty(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        store.get_entries_for_month.return_value = []
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        bridge.receive("journal.loadMonth", json.dumps({"year": 2025, "month": 1}))

        events = {e[0]: e[1] for e in emitted}
        assert events["journal.monthData"] == {"dates": [], "moods": {}}

    def test_load_month_error_emits_empty(self):
        bridge, emitted = _make_bridge_and_capture()
        store = MagicMock()
        store.get_entries_for_month.side_effect = RuntimeError("db error")
        integration = _make_mock_integration(store)

        wire_journal_events(bridge, integration)
        bridge.receive("journal.loadMonth", json.dumps({"year": 2025, "month": 1}))

        events = {e[0]: e[1] for e in emitted}
        assert events["journal.monthData"] == {"dates": [], "moods": {}}
