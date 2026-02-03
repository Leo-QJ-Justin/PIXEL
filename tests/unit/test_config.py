"""Tests for config.py settings management."""

import json
from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestLoadSettings:
    """Tests for load_settings function."""

    def test_load_settings_missing_file_returns_default(self, tmp_path):
        """When settings file doesn't exist, return default structure."""
        with patch("config.SETTINGS_FILE", tmp_path / "nonexistent.json"):
            from config import load_settings

            result = load_settings()

        assert result == {"monitored_users": []}

    def test_load_settings_existing_file(self, temp_settings_with_users):
        """When settings file exists, return its contents."""
        with patch("config.SETTINGS_FILE", temp_settings_with_users):
            from config import load_settings

            result = load_settings()

        assert result == {"monitored_users": [123456789, 987654321]}


@pytest.mark.unit
class TestSaveSettings:
    """Tests for save_settings function."""

    def test_save_settings_writes_json(self, tmp_path):
        """save_settings should write valid JSON to file."""
        settings_file = tmp_path / "settings.json"

        with patch("config.SETTINGS_FILE", settings_file):
            from config import save_settings

            settings = {"monitored_users": [111, 222], "extra_key": "value"}
            save_settings(settings)

        assert settings_file.exists()
        content = json.loads(settings_file.read_text())
        assert content == settings


@pytest.mark.unit
class TestGetMonitoredUsers:
    """Tests for get_monitored_users function."""

    def test_get_monitored_users_empty(self, temp_settings_file):
        """Returns empty list when no users monitored."""
        with patch("config.SETTINGS_FILE", temp_settings_file):
            from config import get_monitored_users

            result = get_monitored_users()

        assert result == []

    def test_get_monitored_users_with_users(self, temp_settings_with_users):
        """Returns list of monitored user IDs."""
        with patch("config.SETTINGS_FILE", temp_settings_with_users):
            from config import get_monitored_users

            result = get_monitored_users()

        assert result == [123456789, 987654321]


@pytest.mark.unit
class TestAddMonitoredUser:
    """Tests for add_monitored_user function."""

    def test_add_monitored_user_new_user(self, temp_settings_file):
        """Adding a new user appends to the list."""
        with patch("config.SETTINGS_FILE", temp_settings_file):
            from config import add_monitored_user, get_monitored_users

            add_monitored_user(555555)
            result = get_monitored_users()

        assert 555555 in result

    def test_add_monitored_user_duplicate(self, temp_settings_with_users):
        """Adding existing user doesn't create duplicates."""
        with patch("config.SETTINGS_FILE", temp_settings_with_users):
            from config import add_monitored_user, get_monitored_users

            add_monitored_user(123456789)  # Already exists
            result = get_monitored_users()

        assert result.count(123456789) == 1


@pytest.mark.unit
class TestRemoveMonitoredUser:
    """Tests for remove_monitored_user function."""

    def test_remove_monitored_user_existing(self, temp_settings_with_users):
        """Removing existing user removes from list."""
        with patch("config.SETTINGS_FILE", temp_settings_with_users):
            from config import get_monitored_users, remove_monitored_user

            remove_monitored_user(123456789)
            result = get_monitored_users()

        assert 123456789 not in result
        assert 987654321 in result

    def test_remove_monitored_user_nonexistent(self, temp_settings_with_users):
        """Removing nonexistent user does nothing."""
        with patch("config.SETTINGS_FILE", temp_settings_with_users):
            from config import get_monitored_users, remove_monitored_user

            remove_monitored_user(999999)  # Doesn't exist
            result = get_monitored_users()

        assert result == [123456789, 987654321]
