import asyncio
import logging
import os
import socket
import sys
from logging.handlers import RotatingFileHandler

from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from config import BASE_DIR, BEHAVIORS_DIR, INTEGRATIONS_DIR, load_settings
from src.core.behavior_registry import BehaviorRegistry
from src.core.integration_manager import IntegrationManager
from src.services.personality_engine import PersonalityEngine
from src.ui.bridge import BridgeHost
from src.ui.panel_host import PanelHost
from src.ui.pet_window import PetWidget
from src.ui.tray_icon import TrayIcon

LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        logs_dir / "pet.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(file_handler)


logger = logging.getLogger(__name__)

# Single-instance lock: bind a local TCP socket on a fixed port.
# If binding fails, another instance is already running.
_INSTANCE_LOCK_PORT = 48721
_instance_lock: socket.socket | None = None


def _acquire_instance_lock() -> bool:
    """Try to acquire a single-instance lock. Returns True if this is the only instance."""
    global _instance_lock
    _instance_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_lock.bind(("127.0.0.1", _INSTANCE_LOCK_PORT))
        _instance_lock.listen(1)
        return True
    except OSError:
        _instance_lock.close()
        _instance_lock = None
        return False


def main():
    setup_logging()

    if not _acquire_instance_lock():
        logger.warning("Another PIXEL instance is already running — exiting.")
        print("PIXEL is already running.", file=sys.stderr)
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    settings = load_settings()
    personality_engine = PersonalityEngine(settings)

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

    pet = PetWidget(behavior_registry, personality_engine=personality_engine)

    # React panel host
    bridge = BridgeHost()
    dev_mode = os.environ.get("PIXEL_DEV_UI") == "1"
    panel_host = PanelHost(bridge, dev_mode=dev_mode)

    tray = TrayIcon(
        pet, integration_manager, behavior_registry,
        panel_host=panel_host,
    )

    journal_integration = integration_manager.get_integration("journal")
    if journal_integration:
        from src.ui.bridge_journal import wire_journal_events

        wire_journal_events(bridge, journal_integration)

    from src.ui.bridge_settings import wire_settings_events

    wire_settings_events(bridge, on_settings_changed=lambda s: tray.settings_changed.emit(s))

    pomodoro_integration = integration_manager.get_integration("pomodoro")
    if pomodoro_integration:
        from src.ui.bridge_pomodoro import wire_pomodoro_events

        wire_pomodoro_events(bridge, pomodoro_integration)

    habits_integration = integration_manager.get_integration("habits")
    if habits_integration:
        from src.ui.bridge_habits import wire_habits_events

        wire_habits_events(bridge, habits_integration)

    # Window control events (always wired)
    def _on_window_minimize(_data):
        panel_host.showMinimized()

    def _on_window_maximize(_data):
        if panel_host.isMaximized():
            panel_host.showNormal()
        else:
            panel_host.showMaximized()

    def _on_window_close(_data):
        panel_host.hide()

    def _on_window_drag_start(data):
        panel_host._drag_active = True
        panel_host._drag_start_pos = QPoint(int(data.get("x", 0)), int(data.get("y", 0)))

    def _on_window_drag_move(data):
        if not panel_host._drag_active:
            return
        current = QPoint(int(data.get("x", 0)), int(data.get("y", 0)))
        delta = current - panel_host._drag_start_pos
        panel_host.move(panel_host.pos() + delta)
        panel_host._drag_start_pos = current

    def _on_window_drag_end(_data):
        panel_host._drag_active = False

    bridge.on("window.minimize", _on_window_minimize)
    bridge.on("window.maximize", _on_window_maximize)
    bridge.on("window.close", _on_window_close)
    bridge.on("window.dragStart", _on_window_drag_start)
    bridge.on("window.dragMove", _on_window_drag_move)
    bridge.on("window.dragEnd", _on_window_drag_end)

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
        want_on_top = general.get("always_on_top", True)
        has_on_top = bool(pet.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
        if want_on_top != has_on_top:
            if want_on_top:
                pet.setWindowFlags(pet.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            else:
                pet.setWindowFlags(pet.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            pet.show()
        personality_engine.update_settings(new_settings)

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
