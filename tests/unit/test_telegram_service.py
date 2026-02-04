"""Tests for TelegramIntegration."""

import pytest


@pytest.mark.unit
class TestTelegramIntegrationInit:
    """Tests for TelegramIntegration initialization."""

    def test_integration_initialization(self, tmp_path):
        """Integration initializes with correct properties."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()
        settings = {"enabled": True, "trigger_behavior": "alert"}

        integration = TelegramIntegration(integration_path, settings)

        assert integration._client is None
        assert integration._last_sender_id is None
        assert integration.enabled is True

    def test_integration_name(self, tmp_path):
        """Integration should have correct name."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {})

        assert integration.name == "telegram"

    def test_integration_display_name(self, tmp_path):
        """Integration should have correct display name."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {})

        assert integration.display_name == "Telegram Notifications"

    def test_default_settings(self, tmp_path):
        """Integration should provide default settings."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {})
        defaults = integration.get_default_settings()

        assert defaults["enabled"] is True
        assert defaults["trigger_behavior"] == "alert"


@pytest.mark.unit
class TestGetLastSenderId:
    """Tests for get_last_sender_id method."""

    def test_get_last_sender_id_initially_none(self, tmp_path):
        """get_last_sender_id returns None when no messages received."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {})

        assert integration.get_last_sender_id() is None

    def test_get_last_sender_id_after_set(self, tmp_path):
        """get_last_sender_id returns the stored sender ID."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {})
        integration._last_sender_id = 123456

        assert integration.get_last_sender_id() == 123456


@pytest.mark.unit
class TestStart:
    """Tests for start method."""

    @pytest.mark.asyncio
    async def test_start_without_credentials_logs_error(self, tmp_path, caplog, monkeypatch):
        """start() logs error and returns when credentials missing."""
        monkeypatch.delenv("API_ID", raising=False)
        monkeypatch.delenv("API_HASH", raising=False)

        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {})
        await integration.start()

        assert "API_ID and API_HASH not configured" in caplog.text
        assert integration._client is None


@pytest.mark.unit
class TestStop:
    """Tests for stop method."""

    @pytest.mark.asyncio
    async def test_stop_when_not_connected(self, tmp_path):
        """stop() does nothing when client is None."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {})

        # Should not raise
        await integration.stop()
        assert integration._client is None

    @pytest.mark.asyncio
    async def test_stop_when_connected(self, tmp_path, mock_telegram_client):
        """stop() calls client.disconnect when connected."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {})
        integration._client = mock_telegram_client

        await integration.stop()

        mock_telegram_client.disconnect.assert_awaited_once()
        assert integration._client is None


@pytest.mark.unit
class TestEnabledProperty:
    """Tests for enabled property."""

    def test_enabled_from_settings(self, tmp_path):
        """enabled should reflect settings value."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {"enabled": False})

        assert integration.enabled is False

    def test_enabled_can_be_set(self, tmp_path):
        """enabled property should be settable."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {"enabled": True})
        integration.enabled = False

        assert integration.enabled is False


@pytest.mark.unit
class TestTrigger:
    """Tests for trigger method."""

    def test_trigger_emits_signal(self, tmp_path):
        """trigger() should emit request_behavior signal."""
        from integrations.telegram.integration import TelegramIntegration

        integration_path = tmp_path / "telegram"
        integration_path.mkdir()

        integration = TelegramIntegration(integration_path, {})

        # Track signal emission
        received = []
        integration.request_behavior.connect(lambda name, ctx: received.append((name, ctx)))

        integration.trigger("alert", {"sender": "Test"})

        assert len(received) == 1
        assert received[0][0] == "alert"
        assert received[0][1] == {"sender": "Test"}
