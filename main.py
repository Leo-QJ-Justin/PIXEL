import asyncio
import logging
import sys

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from src.services.telegram_service import TelegramService
from src.ui.haro_window import HaroWidget
from src.ui.tray_icon import TrayIcon

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    # 1. Setup App & Loop
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 2. Init Components
    haro = HaroWidget()
    tray = TrayIcon(haro)
    bot = TelegramService()

    # 3. Connect Signals
    # When bot sees a message -> Haro gets excited
    bot.message_received.connect(haro.trigger_alert)
    logger.info("Signal connected: bot.message_received -> haro.trigger_alert")

    # 4. Start Bot (Non-blocking task)
    loop.create_task(bot.start())
    logger.info("Telegram bot task created")

    # 5. Show Window and Tray
    haro.show()
    tray.show()

    # 6. Run Loop
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
