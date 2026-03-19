"""Tests for Google Calendar auth module."""

import json

import pytest


@pytest.mark.unit
class TestGetClientConfig:
    """Tests for _get_client_config."""

    def test_returns_config_with_env_vars(self, monkeypatch):
        from integrations.google_calendar.auth import _get_client_config

        monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_SECRET", "test-client-secret")

        config = _get_client_config()

        assert config is not None
        assert config["installed"]["client_id"] == "test-client-id"
        assert config["installed"]["client_secret"] == "test-client-secret"
        assert "auth_uri" in config["installed"]
        assert "token_uri" in config["installed"]

    def test_uses_bundled_defaults_without_env_vars(self, monkeypatch):
        from integrations.google_calendar.auth import (
            _DEFAULT_CLIENT_ID,
            _DEFAULT_CLIENT_SECRET,
            _get_client_config,
        )

        monkeypatch.delenv("GOOGLE_CALENDAR_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CALENDAR_CLIENT_SECRET", raising=False)

        config = _get_client_config()

        assert config is not None
        assert config["installed"]["client_id"] == _DEFAULT_CLIENT_ID
        assert config["installed"]["client_secret"] == _DEFAULT_CLIENT_SECRET

    def test_env_vars_override_defaults(self, monkeypatch):
        from integrations.google_calendar.auth import _get_client_config

        monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_ID", "custom-id")
        monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_SECRET", "custom-secret")

        config = _get_client_config()

        assert config["installed"]["client_id"] == "custom-id"
        assert config["installed"]["client_secret"] == "custom-secret"

    def test_empty_env_vars_fall_back_to_defaults(self, monkeypatch):
        from integrations.google_calendar.auth import (
            _DEFAULT_CLIENT_ID,
            _DEFAULT_CLIENT_SECRET,
            _get_client_config,
        )

        monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_ID", "")
        monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_SECRET", "")

        config = _get_client_config()

        assert config["installed"]["client_id"] == _DEFAULT_CLIENT_ID
        assert config["installed"]["client_secret"] == _DEFAULT_CLIENT_SECRET


@pytest.mark.unit
class TestLoadCredentials:
    """Tests for load_credentials."""

    def test_returns_none_when_no_file(self, tmp_path):
        from integrations.google_calendar.auth import load_credentials

        result = load_credentials(tmp_path)
        assert result is None

    def test_returns_none_for_invalid_json(self, tmp_path):
        from integrations.google_calendar.auth import load_credentials

        token_path = tmp_path / "google_calendar_token.json"
        token_path.write_text("not valid json{{{")

        result = load_credentials(tmp_path)
        assert result is None

    def test_loads_valid_credentials(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch

        from integrations.google_calendar.auth import load_credentials

        mock_creds = MagicMock()
        mock_creds.valid = True

        token_path = tmp_path / "google_calendar_token.json"
        token_data = {
            "token": "fake-token",
            "refresh_token": "fake-refresh",
            "client_id": "test-id",
            "client_secret": "test-secret",
        }
        token_path.write_text(json.dumps(token_data))

        with patch(
            "integrations.google_calendar.auth.Credentials.from_authorized_user_file",
            return_value=mock_creds,
        ):
            result = load_credentials(tmp_path)

        assert result is mock_creds

    def test_refreshes_expired_credentials(self, tmp_path):
        from unittest.mock import MagicMock, patch

        from integrations.google_calendar.auth import load_credentials

        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "fake-refresh"
        mock_creds.to_json.return_value = '{"token": "refreshed"}'

        token_path = tmp_path / "google_calendar_token.json"
        token_path.write_text(json.dumps({"token": "old"}))

        with patch(
            "integrations.google_calendar.auth.Credentials.from_authorized_user_file",
            return_value=mock_creds,
        ):
            result = load_credentials(tmp_path)

        assert result is mock_creds
        mock_creds.refresh.assert_called_once()

    def test_returns_none_on_refresh_failure(self, tmp_path):
        from unittest.mock import MagicMock, patch

        from google.auth.exceptions import RefreshError

        from integrations.google_calendar.auth import load_credentials

        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "fake-refresh"
        mock_creds.refresh.side_effect = RefreshError("token revoked")

        token_path = tmp_path / "google_calendar_token.json"
        token_path.write_text(json.dumps({"token": "old"}))

        with patch(
            "integrations.google_calendar.auth.Credentials.from_authorized_user_file",
            return_value=mock_creds,
        ):
            result = load_credentials(tmp_path)

        assert result is None


@pytest.mark.unit
class TestIsAuthenticated:
    """Tests for is_authenticated."""

    def test_returns_false_when_no_file(self, tmp_path):
        from integrations.google_calendar.auth import is_authenticated

        assert is_authenticated(tmp_path) is False

    def test_returns_false_for_invalid_json(self, tmp_path):
        from integrations.google_calendar.auth import is_authenticated

        token_path = tmp_path / "google_calendar_token.json"
        token_path.write_text("not json{{{")

        assert is_authenticated(tmp_path) is False

    def test_returns_true_for_valid_credentials(self, tmp_path):
        from unittest.mock import MagicMock, patch

        from integrations.google_calendar.auth import is_authenticated

        mock_creds = MagicMock()
        mock_creds.valid = True

        token_path = tmp_path / "google_calendar_token.json"
        token_path.write_text(json.dumps({"token": "fake"}))

        with patch(
            "integrations.google_calendar.auth.Credentials.from_authorized_user_file",
            return_value=mock_creds,
        ):
            assert is_authenticated(tmp_path) is True

    def test_returns_true_for_expired_with_refresh_token(self, tmp_path):
        from unittest.mock import MagicMock, patch

        from integrations.google_calendar.auth import is_authenticated

        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "fake-refresh"

        token_path = tmp_path / "google_calendar_token.json"
        token_path.write_text(json.dumps({"token": "fake"}))

        with patch(
            "integrations.google_calendar.auth.Credentials.from_authorized_user_file",
            return_value=mock_creds,
        ):
            assert is_authenticated(tmp_path) is True


@pytest.mark.unit
class TestClearCredentials:
    """Tests for clear_credentials."""

    def test_deletes_token_file(self, tmp_path):
        from integrations.google_calendar.auth import clear_credentials

        token_path = tmp_path / "google_calendar_token.json"
        token_path.write_text('{"token": "test"}')

        clear_credentials(tmp_path)

        assert not token_path.exists()

    def test_no_error_when_no_file(self, tmp_path):
        from integrations.google_calendar.auth import clear_credentials

        clear_credentials(tmp_path)  # Should not raise
