"""Tests for UsageTracker — file-based quota counter with monthly reset."""

import json
import threading

import pytest


def _make_tracker(tmp_path, quota_limit=9500):
    """Helper to create a UsageTracker with a temp file."""
    from integrations.google_calendar.usage_tracker import UsageTracker

    usage_file = tmp_path / "api_usage.json"
    return UsageTracker(usage_file=usage_file, quota_limit=quota_limit)


@pytest.mark.unit
class TestUsageTrackerInit:
    """Tests for UsageTracker initialization."""

    def test_initialization_creates_empty_data(self, tmp_path):
        tracker = _make_tracker(tmp_path)
        # Should have at minimum a "month" key after init
        assert "month" in tracker._data

    def test_initialization_creates_file(self, tmp_path):
        usage_file = tmp_path / "api_usage.json"
        assert not usage_file.exists()
        _make_tracker(tmp_path)
        assert usage_file.exists()


@pytest.mark.unit
class TestCanCall:
    """Tests for can_call method."""

    def test_returns_true_when_under_limit(self, tmp_path):
        tracker = _make_tracker(tmp_path, quota_limit=100)
        assert tracker.can_call("routes_api") is True

    def test_returns_false_when_at_limit(self, tmp_path):
        tracker = _make_tracker(tmp_path, quota_limit=3)
        # Manually set the count to the limit
        tracker._data["routes_api"] = 3
        assert tracker.can_call("routes_api") is False

    def test_returns_false_when_over_limit(self, tmp_path):
        tracker = _make_tracker(tmp_path, quota_limit=3)
        tracker._data["routes_api"] = 5
        assert tracker.can_call("routes_api") is False

    def test_returns_true_for_different_api(self, tmp_path):
        tracker = _make_tracker(tmp_path, quota_limit=3)
        tracker._data["routes_api"] = 3
        # geocoding_api is separate, should still be under limit
        assert tracker.can_call("geocoding_api") is True


@pytest.mark.unit
class TestIncrement:
    """Tests for increment method."""

    def test_increases_count(self, tmp_path):
        tracker = _make_tracker(tmp_path)
        tracker.increment("routes_api")
        assert tracker._data["routes_api"] == 1

    def test_multiple_increments(self, tmp_path):
        tracker = _make_tracker(tmp_path)
        tracker.increment("routes_api")
        tracker.increment("routes_api")
        tracker.increment("routes_api")
        assert tracker._data["routes_api"] == 3

    def test_persists_to_file(self, tmp_path):
        usage_file = tmp_path / "api_usage.json"

        from integrations.google_calendar.usage_tracker import UsageTracker

        tracker = UsageTracker(usage_file=usage_file, quota_limit=9500)
        tracker.increment("routes_api")
        tracker.increment("routes_api")

        # Read file directly to verify persistence
        with open(usage_file) as f:
            data = json.load(f)
        assert data["routes_api"] == 2


@pytest.mark.unit
class TestMonthlyReset:
    """Tests for monthly reset behavior."""

    def test_resets_when_month_changes(self, tmp_path):
        usage_file = tmp_path / "api_usage.json"

        from integrations.google_calendar.usage_tracker import UsageTracker

        # Write usage data with a different (old) month
        old_data = {"month": "2020-01", "routes_api": 500, "geocoding_api": 200}
        with open(usage_file, "w") as f:
            json.dump(old_data, f)

        # Creating a tracker should detect the month mismatch and reset
        tracker = UsageTracker(usage_file=usage_file, quota_limit=9500)

        # After reset, API counters should be gone and month should be current
        assert tracker._data.get("routes_api", 0) == 0
        assert tracker._data.get("geocoding_api", 0) == 0
        assert tracker._data["month"] != "2020-01"

    def test_no_reset_when_same_month(self, tmp_path):
        from datetime import datetime

        usage_file = tmp_path / "api_usage.json"

        from integrations.google_calendar.usage_tracker import UsageTracker

        current_month = datetime.now().strftime("%Y-%m")
        existing_data = {"month": current_month, "routes_api": 42}
        with open(usage_file, "w") as f:
            json.dump(existing_data, f)

        tracker = UsageTracker(usage_file=usage_file, quota_limit=9500)
        assert tracker._data["routes_api"] == 42


@pytest.mark.unit
class TestGetUsage:
    """Tests for get_usage method."""

    def test_returns_correct_dict(self, tmp_path):
        tracker = _make_tracker(tmp_path, quota_limit=5000)
        tracker.increment("routes_api")
        tracker.increment("routes_api")
        tracker.increment("geocoding_api")

        usage = tracker.get_usage()
        assert usage["routes_api"] == 2
        assert usage["geocoding_api"] == 1
        assert usage["limit"] == 5000
        assert "month" in usage

    def test_returns_zero_for_unused_apis(self, tmp_path):
        tracker = _make_tracker(tmp_path)
        usage = tracker.get_usage()
        assert usage["routes_api"] == 0
        assert usage["geocoding_api"] == 0


@pytest.mark.unit
class TestCorruptedFile:
    """Tests for corrupted file handling."""

    def test_corrupted_json_recovers_gracefully(self, tmp_path):
        usage_file = tmp_path / "api_usage.json"
        usage_file.write_text("{{not valid json!!")

        from integrations.google_calendar.usage_tracker import UsageTracker

        # Should not raise; should reset to empty
        tracker = UsageTracker(usage_file=usage_file, quota_limit=9500)
        assert "month" in tracker._data
        assert tracker.can_call("routes_api") is True

    def test_empty_file_recovers_gracefully(self, tmp_path):
        usage_file = tmp_path / "api_usage.json"
        usage_file.write_text("")

        from integrations.google_calendar.usage_tracker import UsageTracker

        tracker = UsageTracker(usage_file=usage_file, quota_limit=9500)
        assert "month" in tracker._data


@pytest.mark.unit
class TestThreadSafety:
    """Basic thread safety checks."""

    def test_concurrent_increments(self, tmp_path):
        tracker = _make_tracker(tmp_path, quota_limit=100000)
        errors = []

        def increment_many():
            try:
                for _ in range(100):
                    tracker.increment("routes_api")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=increment_many) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert tracker._data["routes_api"] == 500
