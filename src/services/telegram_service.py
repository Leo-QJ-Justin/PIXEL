import logging

from PyQt6.QtCore import Q_ARG, QMetaObject, QObject, Qt, pyqtSignal, pyqtSlot
from telethon import TelegramClient, events

from config import API_HASH, API_ID, add_monitored_user, get_monitored_users

logger = logging.getLogger(__name__)


class TelegramService(QObject):
    """Service for handling Telegram messages."""

    # Signal emitted when a message is received from a monitored user
    message_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._client = None
        self._last_sender_id = None

    @pyqtSlot(str)
    def _emit_signal(self, sender_name: str):
        """Thread-safe signal emission."""
        logger.debug(f"Emitting signal for: {sender_name}")
        self.message_received.emit(sender_name)

    async def start(self):
        """Start the Telegram client and listen for messages."""
        if not API_ID or not API_HASH:
            logger.error("API_ID and API_HASH not configured in .env file")
            return

        self._client = TelegramClient("haro_session", API_ID, API_HASH)

        @self._client.on(events.NewMessage(incoming=True))
        async def handle_new_message(event):
            sender = await event.get_sender()
            sender_id = event.sender_id
            self._last_sender_id = sender_id
            logger.debug(f"Message from ID: {sender_id}")

            # Check if sender is in monitored list
            monitored_users = get_monitored_users()
            if sender_id in monitored_users:
                sender_name = getattr(sender, "first_name", "Unknown")
                logger.info(f"Monitored user detected: {sender_name}")
                # Use QMetaObject.invokeMethod for thread-safe signal emission
                QMetaObject.invokeMethod(
                    self,
                    "_emit_signal",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, sender_name),
                )
            else:
                logger.debug(f"Sender {sender_id} not monitored, ignoring")

        await self._client.start()
        logger.info("Telegram service started. Listening for messages...")
        await self._client.run_until_disconnected()

    def add_last_sender_to_watchlist(self):
        """Add the last message sender to the monitored users list."""
        if self._last_sender_id:
            add_monitored_user(self._last_sender_id)
            return True
        return False

    def get_last_sender_id(self):
        """Get the ID of the last message sender."""
        return self._last_sender_id

    async def disconnect(self):
        """Disconnect the Telegram client."""
        if self._client:
            await self._client.disconnect()
