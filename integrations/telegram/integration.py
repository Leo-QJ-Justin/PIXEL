"""Telegram integration for monitoring messages from VIP contacts."""

import logging
import os
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Q_ARG, QMetaObject, Qt, pyqtSlot
from telethon import TelegramClient, events

from src.core.base_integration import BaseIntegration

logger = logging.getLogger(__name__)


class TelegramIntegration(BaseIntegration):
    """Monitors Telegram for messages from VIP contacts."""

    def __init__(self, integration_path: Path, settings: dict[str, Any]):
        super().__init__(integration_path, settings)
        self._client: TelegramClient | None = None
        self._last_sender_id: int | None = None
        self._running = False

    @property
    def name(self) -> str:
        return "telegram"

    @property
    def display_name(self) -> str:
        return "Telegram Notifications"

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "trigger_behavior": "alert",
        }

    @pyqtSlot(str, str)
    def _emit_behavior(self, behavior_name: str, context_str: str):
        """Thread-safe behavior trigger."""
        import json

        context = json.loads(context_str) if context_str else {}
        logger.debug(f"Emitting behavior: {behavior_name} with context {context}")
        self.trigger(behavior_name, context)

    async def start(self) -> None:
        """Start the Telegram client and listen for messages."""
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")

        if not api_id or not api_hash:
            logger.error("API_ID and API_HASH not configured in .env file")
            return

        # Get monitored users from environment
        from config import get_monitored_users

        monitored_users = get_monitored_users()

        self._client = TelegramClient("haro_session", api_id, api_hash)

        # Connect first to check authorization status
        await self._client.connect()

        if not await self._client.is_user_authorized():
            logger.error(
                "Telegram session not authorized. "
                "Run 'uv run python scripts/auth_telegram.py' to authenticate first."
            )
            await self._client.disconnect()
            self._client = None
            return

        self._running = True

        @self._client.on(events.NewMessage(incoming=True))
        async def handle_new_message(event):
            if not self._running:
                return

            sender = await event.get_sender()
            sender_id = event.sender_id
            self._last_sender_id = sender_id
            logger.debug(f"Message from ID: {sender_id}")

            # Check if sender is in monitored list
            if sender_id in monitored_users:
                sender_name = getattr(sender, "first_name", "Unknown")
                logger.info(f"Monitored user detected: {sender_name}")

                # Get configured trigger behavior
                trigger_behavior = self._settings.get("trigger_behavior", "alert")

                # Use QMetaObject.invokeMethod for thread-safe signal emission
                import json

                context = json.dumps({"sender": sender_name, "sender_id": sender_id})
                QMetaObject.invokeMethod(
                    self,
                    "_emit_behavior",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, trigger_behavior),
                    Q_ARG(str, context),
                )
            else:
                logger.debug(f"Sender {sender_id} not monitored, ignoring")

        logger.info("Telegram integration started. Listening for messages...")

    async def stop(self) -> None:
        """Stop the Telegram client."""
        self._running = False
        if self._client:
            await self._client.disconnect()
            self._client = None
        logger.info("Telegram integration stopped")

    def get_last_sender_id(self) -> int | None:
        """Get the ID of the last message sender."""
        return self._last_sender_id
