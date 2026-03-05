import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from config import BASE_DIR, BEHAVIORS_DIR, INTEGRATIONS_DIR, load_settings
from src.core.behavior_registry import BehaviorRegistry
from src.core.integration_manager import IntegrationManager
from src.ui.pet_window import PetWidget
from src.ui.tray_icon import TrayIcon

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        LOGS_DIR / "pet.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(file_handler)


setup_logging()
logger = logging.getLogger(__name__)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    settings = load_settings()

    sprites_face_left = settings.get("general", {}).get("sprite_default_facing", "right") == "left"
    behavior_registry = BehaviorRegistry(sprites_face_left=sprites_face_left)
    core_behaviors = behavior_registry.discover_behaviors([BEHAVIORS_DIR])
    logger.info(f"Loaded core behaviors: {core_behaviors}")

    integration_manager = IntegrationManager(
        integrations_path=INTEGRATIONS_DIR,
        behavior_registry=behavior_registry,
        settings=settings,
    )

    discovered = integration_manager.discover()
    logger.info(f"Discovered integrations: {discovered}")

    for name in discovered:
        integration_manager.load(name)

    pet = PetWidget(behavior_registry)

    # Create Pomodoro widget if integration is loaded
    pomodoro_widget = None
    pomodoro = integration_manager.get_integration("pomodoro")
    if pomodoro:
        from src.ui.pomodoro_widget import PomodoroWidget

        pomodoro_widget = PomodoroWidget(pomodoro)
        logger.info("Pomodoro widget created")

    tray = TrayIcon(pet, integration_manager, behavior_registry, pomodoro_widget=pomodoro_widget)

    # Let integrations wire their own UI via setup_ui hook
    integration_manager.setup_all_ui(pet)

    # Wire integration notifications to speech bubble
    integration_manager.notification_requested.connect(
        lambda ctx: pet.show_bubble(ctx.get("bubble_text", ""), ctx.get("bubble_duration_ms", 5000))
    )

    # Propagate settings changes at runtime
    def _on_settings_changed(new_settings: dict):
        from PyQt6.QtCore import Qt

        from src.utils.startup import set_startup_enabled

        general = new_settings.get("general", {})
        set_startup_enabled(general.get("start_on_boot", False))
        if general.get("always_on_top", True):
            pet.setWindowFlags(pet.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            pet.setWindowFlags(pet.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        pet.show()

    tray.settings_changed.connect(_on_settings_changed)

    loop.create_task(integration_manager.start_all_enabled())
    logger.info("Integration startup tasks created")

    pet.show()
    tray.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
