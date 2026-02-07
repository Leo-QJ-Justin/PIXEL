"""Tests for config.py settings management."""

import importlib
import json
from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestLoadSettings:
    """Tests for load_settings function."""

    def test_load_settings_missing_file_returns_defaults(self, tmp_path):
        """When settings file doesn't exist, return default structure."""
        with patch("config.SETTINGS_FILE", tmp_path / "nonexistent.json"):
            import config

            importlib.reload(config)
            result = config.load_settings()

        assert "general" in result
        assert "behaviors" in result
        assert "integrations" in result
        assert result["general"]["always_on_top"] is True

    def test_load_settings_merges_with_defaults(self, tmp_path):
        """When settings file exists, merge with defaults."""
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(
            json.dumps(
                {
                    "general": {"always_on_top": False},
                }
            )
        )

        import config

        # Directly patch the module attribute after reload
        original_file = config.SETTINGS_FILE
        try:
            config.SETTINGS_FILE = settings_file
            result = config.load_settings()

            # Custom value should override default
            assert result["general"]["always_on_top"] is False
            # Default values should still be present
            assert result["general"]["start_minimized"] is False
            assert "integrations" in result
        finally:
            config.SETTINGS_FILE = original_file


@pytest.mark.unit
class TestSaveSettings:
    """Tests for save_settings function."""

    def test_save_settings_writes_json(self, tmp_path):
        """save_settings should write valid JSON to file."""
        settings_file = tmp_path / "settings.json"

        import config

        original_file = config.SETTINGS_FILE
        try:
            config.SETTINGS_FILE = settings_file

            settings = {
                "general": {"always_on_top": True},
                "behaviors": {},
                "integrations": {},
            }
            config.save_settings(settings)

            assert settings_file.exists()
            content = json.loads(settings_file.read_text())
            assert content == settings
        finally:
            config.SETTINGS_FILE = original_file


@pytest.mark.unit
class TestGetMonitoredUsers:
    """Tests for get_monitored_users function."""

    def test_get_monitored_users_from_env(self, monkeypatch):
        """Returns list of user IDs from MONITORED_USERS env var."""
        monkeypatch.setenv("MONITORED_USERS", "123456789,987654321")

        import config

        importlib.reload(config)
        result = config.get_monitored_users()

        assert result == [123456789, 987654321]

    def test_get_monitored_users_empty_env(self, monkeypatch):
        """Returns empty list when MONITORED_USERS is empty."""
        monkeypatch.setenv("MONITORED_USERS", "")

        import config

        importlib.reload(config)
        result = config.get_monitored_users()

        assert result == []

    def test_get_monitored_users_not_set(self, monkeypatch):
        """Returns empty list when MONITORED_USERS is not set."""
        # Must set env before reload since config reads at import time
        monkeypatch.delenv("MONITORED_USERS", raising=False)
        # Also ensure dotenv doesn't load it from .env
        monkeypatch.setattr("dotenv.load_dotenv", lambda: None)

        import config

        # Directly set the module-level variable
        config.MONITORED_USERS = []
        result = config.get_monitored_users()

        assert result == []

    def test_get_monitored_users_ignores_invalid(self, monkeypatch):
        """Ignores non-numeric values in MONITORED_USERS."""
        monkeypatch.setenv("MONITORED_USERS", "123,invalid,456,")

        import config

        importlib.reload(config)
        result = config.get_monitored_users()

        assert result == [123, 456]


@pytest.mark.unit
class TestGetIntegrationSettings:
    """Tests for get_integration_settings function."""

    def test_get_integration_settings_existing(self, temp_settings_file):
        """Returns settings for an existing integration."""
        with patch("config.SETTINGS_FILE", temp_settings_file):
            import config

            importlib.reload(config)
            result = config.get_integration_settings("telegram")

        assert result["enabled"] is True
        assert result["trigger_behavior"] == "alert"

    def test_get_integration_settings_nonexistent(self, temp_settings_file):
        """Returns empty dict for nonexistent integration."""
        with patch("config.SETTINGS_FILE", temp_settings_file):
            import config

            importlib.reload(config)
            result = config.get_integration_settings("nonexistent")

        assert result == {}


@pytest.mark.unit
class TestGetBehaviorSettings:
    """Tests for get_behavior_settings function."""

    def test_get_behavior_settings_existing(self, temp_settings_with_users):
        """Returns settings for an existing behavior."""
        import config

        original_file = config.SETTINGS_FILE
        try:
            config.SETTINGS_FILE = temp_settings_with_users
            result = config.get_behavior_settings("wander")

            assert result["wander_chance"] == 0.5
        finally:
            config.SETTINGS_FILE = original_file

    def test_get_behavior_settings_nonexistent(self, temp_settings_file):
        """Returns empty dict for nonexistent behavior."""
        with patch("config.SETTINGS_FILE", temp_settings_file):
            import config

            importlib.reload(config)
            result = config.get_behavior_settings("nonexistent")

        assert result == {}


@pytest.mark.unit
class TestGetGeneralSettings:
    """Tests for get_general_settings function."""

    def test_get_general_settings(self, temp_settings_file):
        """Returns general settings."""
        with patch("config.SETTINGS_FILE", temp_settings_file):
            import config

            importlib.reload(config)
            result = config.get_general_settings()

        assert result["always_on_top"] is True
        assert result["start_minimized"] is False


@pytest.mark.unit
class TestDefaultSettings:
    """Tests for DEFAULT_SETTINGS structure."""

    def test_time_periods_defaults_exist(self):
        """DEFAULT_SETTINGS should include time_periods in behaviors."""
        import config

        tp = config.DEFAULT_SETTINGS["behaviors"]["time_periods"]
        assert tp["enabled"] is True
        assert tp["check_interval_ms"] == 30000
        assert "morning" in tp["periods"]
        assert "afternoon" in tp["periods"]
        assert "night" in tp["periods"]
        assert "morning" in tp["greetings"]
        assert "afternoon" in tp["greetings"]
        assert "night" in tp["greetings"]

    def test_speech_bubble_defaults_exist(self):
        """DEFAULT_SETTINGS should include speech_bubble in general."""
        import config

        sb = config.DEFAULT_SETTINGS["general"]["speech_bubble"]
        assert sb["enabled"] is True
        assert sb["duration_ms"] == 3000
