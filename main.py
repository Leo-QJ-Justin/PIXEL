import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from config import BASE_DIR, BEHAVIORS_DIR, INTEGRATIONS_DIR, load_settings
from src.core.behavior_registry import BehaviorRegistry
from src.core.integration_manager import IntegrationManager
from src.ui.haro_window import HaroWidget
from src.ui.tray_icon import TrayIcon

# Configure logging
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Configure logging to both console and rotating file."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Console handler (INFO level to reduce noise)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # File handler (DEBUG level for detailed logs)
    file_handler = RotatingFileHandler(
        LOGS_DIR / "haro.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(file_handler)


setup_logging()
logger = logging.getLogger(__name__)


def main():
    # 1. Setup App & Loop
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 2. Load settings
    settings = load_settings()

    # 3. Initialize behavior registry and discover core behaviors
    behavior_registry = BehaviorRegistry()
    core_behaviors = behavior_registry.discover_behaviors([BEHAVIORS_DIR])
    logger.info(f"Loaded core behaviors: {core_behaviors}")

    # 4. Initialize integration manager
    integration_manager = IntegrationManager(
        integrations_path=INTEGRATIONS_DIR,
        behavior_registry=behavior_registry,
        settings=settings,
    )

    # 5. Discover and load integrations (also loads their behaviors)
    discovered = integration_manager.discover()
    logger.info(f"Discovered integrations: {discovered}")

    for name in discovered:
        integration_manager.load(name)

    # 6. Create UI components
    haro = HaroWidget(behavior_registry)
    tray = TrayIcon(haro, integration_manager, behavior_registry)

    # 7. Start all enabled integrations
    loop.create_task(integration_manager.start_all_enabled())
    logger.info("Integration startup tasks created")

    # 8. Show window and tray
    haro.show()
    tray.show()

    # 9. Run event loop
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
