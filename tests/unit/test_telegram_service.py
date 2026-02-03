"""Tests for TelegramService."""

from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestTelegramServiceInit:
    """Tests for TelegramService initialization."""

    def test_service_initialization(self):
        """Service initializes with None client and sender."""
        with patch("src.services.telegram_service.API_ID", "test_id"):
            with patch("src.services.telegram_service.API_HASH", "test_hash"):
                from src.services.telegram_service import TelegramService

                service = TelegramService()

        assert service._client is None
        assert service._last_sender_id is None


@pytest.mark.unit
class TestGetLastSenderId:
    """Tests for get_last_sender_id method."""

    def test_get_last_sender_id_initially_none(self):
        """get_last_sender_id returns None when no messages received."""
        with patch("src.services.telegram_service.API_ID", "test_id"):
            with patch("src.services.telegram_service.API_HASH", "test_hash"):
                from src.services.telegram_service import TelegramService

                service = TelegramService()

        assert service.get_last_sender_id() is None

    def test_get_last_sender_id_after_set(self):
        """get_last_sender_id returns the stored sender ID."""
        with patch("src.services.telegram_service.API_ID", "test_id"):
            with patch("src.services.telegram_service.API_HASH", "test_hash"):
                from src.services.telegram_service import TelegramService

                service = TelegramService()
                service._last_sender_id = 123456

        assert service.get_last_sender_id() == 123456


@pytest.mark.unit
class TestAddLastSenderToWatchlist:
    """Tests for add_last_sender_to_watchlist method."""

    def test_add_last_sender_when_none(self):
        """Returns False when no last sender exists."""
        with patch("src.services.telegram_service.API_ID", "test_id"):
            with patch("src.services.telegram_service.API_HASH", "test_hash"):
                from src.services.telegram_service import TelegramService

                service = TelegramService()

        result = service.add_last_sender_to_watchlist()
        assert result is False

    def test_add_last_sender_when_exists(self):
        """Returns True and adds user when last sender exists."""
        with patch("src.services.telegram_service.API_ID", "test_id"):
            with patch("src.services.telegram_service.API_HASH", "test_hash"):
                with patch("src.services.telegram_service.add_monitored_user") as mock_add:
                    from src.services.telegram_service import TelegramService

                    service = TelegramService()
                    service._last_sender_id = 999888

                    result = service.add_last_sender_to_watchlist()

        assert result is True
        mock_add.assert_called_once_with(999888)


@pytest.mark.unit
class TestStart:
    """Tests for start method."""

    @pytest.mark.asyncio
    async def test_start_without_credentials_logs_error(self, caplog):
        """start() logs error and returns when credentials missing."""
        with patch("src.services.telegram_service.API_ID", None):
            with patch("src.services.telegram_service.API_HASH", None):
                from src.services.telegram_service import TelegramService

                service = TelegramService()

                await service.start()

        assert "API_ID and API_HASH not configured" in caplog.text
        assert service._client is None


@pytest.mark.unit
class TestDisconnect:
    """Tests for disconnect method."""

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        """disconnect() does nothing when client is None."""
        with patch("src.services.telegram_service.API_ID", "test_id"):
            with patch("src.services.telegram_service.API_HASH", "test_hash"):
                from src.services.telegram_service import TelegramService

                service = TelegramService()

                # Should not raise
                await service.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_when_connected(self, mock_telegram_client):
        """disconnect() calls client.disconnect when connected."""
        with patch("src.services.telegram_service.API_ID", "test_id"):
            with patch("src.services.telegram_service.API_HASH", "test_hash"):
                from src.services.telegram_service import TelegramService

                service = TelegramService()
                service._client = mock_telegram_client

                await service.disconnect()

        mock_telegram_client.disconnect.assert_awaited_once()
