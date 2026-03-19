"""Panel host window that embeds the React UI in a QWebEngineView."""

import logging
from pathlib import Path

from PyQt6.QtCore import QFile, QPoint, Qt, QTimer, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEngineScript
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMainWindow

from src.ui.bridge import BridgeHost

logger = logging.getLogger(__name__)

# Project root is three levels up from this file (src/ui/panel_host.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class PanelHost(QMainWindow):
    """QMainWindow wrapper that hosts the React frontend in a QWebEngineView.

    In dev mode the view loads from the Vite dev server; in production it
    loads the built ``ui/dist/index.html`` bundle.
    """

    def __init__(self, bridge: BridgeHost, dev_mode: bool = False) -> None:
        super().__init__()
        self._bridge = bridge
        self._dev_mode = dev_mode

        self._setup_window()
        self._setup_web_view()
        self._setup_channel()
        self._load_content()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configure window title, size, and constraints."""
        self.setWindowTitle("PIXEL")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        # Size to 50% of screen width, 75% of screen height for a comfortable dashboard feel
        from PyQt6.QtWidgets import QApplication

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            w = max(700, int(geo.width() * 0.5))
            h = max(600, int(geo.height() * 0.75))
            self.resize(w, h)
        else:
            self.resize(800, 850)
        self.setMinimumSize(550, 600)

        # Drag state for custom title bar
        self._drag_active = False
        self._drag_start_pos = QPoint()
        # Window icon
        icon_path = _PROJECT_ROOT / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _setup_web_view(self) -> None:
        """Create the QWebEngineView and set it as central widget."""
        self._view = QWebEngineView(self)
        self._view.setUpdatesEnabled(True)
        self.setCentralWidget(self._view)

        # Debounce resize: hide the web view during rapid resizing to avoid
        # expensive re-layouts on every pixel, then show it once settled.
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(80)
        self._resize_timer.timeout.connect(self._on_resize_done)

    def _setup_channel(self) -> None:
        """Wire up QWebChannel so the JS side can talk to BridgeHost."""
        self._inject_qwebchannel_script()
        self._channel = QWebChannel(self._view.page())
        self._channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(self._channel)

    def _inject_qwebchannel_script(self) -> None:
        """Inject qwebchannel.js from Qt resources so the JS side can use QWebChannel."""
        f = QFile(":/qtwebchannel/qwebchannel.js")
        f.open(QFile.OpenModeFlag.ReadOnly)
        source = f.readAll().data().decode()
        f.close()

        script = QWebEngineScript()
        script.setName("qwebchannel")
        script.setSourceCode(source)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(False)
        self._view.page().scripts().insert(script)

    def _load_content(self) -> None:
        """Load either the Vite dev server or the production bundle."""
        if self._dev_mode:
            url = QUrl("http://localhost:5173")
            logger.info("Loading React UI from Vite dev server: %s", url.toString())
        else:
            index_path = _PROJECT_ROOT / "ui" / "dist" / "index.html"
            url = QUrl.fromLocalFile(str(index_path))
            logger.info("Loading React UI from: %s", url.toString())
        self._view.load(url)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_panel(self, panel: str) -> None:
        """Show the window, raise it, and navigate to the requested panel."""
        self.show()
        self.raise_()
        self.activateWindow()
        self._center_on_screen()
        # Dual navigation: set hash directly (works before React mounts)
        # AND emit bridge event (works when React is already running)
        self._view.page().runJavaScript(f"window.location.hash = '#/{panel}';")
        self._bridge.emit("window.navigateTo", {"route": f"/{panel}"})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def resizeEvent(self, event) -> None:
        """Debounce resize to reduce QWebEngineView re-layout thrashing."""
        if not self._resize_timer.isActive():
            self._view.setUpdatesEnabled(False)
        self._resize_timer.start()
        super().resizeEvent(event)

    def _on_resize_done(self) -> None:
        """Re-enable web view updates after resize settles."""
        self._view.setUpdatesEnabled(True)
        self._view.update()

    def _center_on_screen(self) -> None:
        """Center the window on the current screen."""
        screen = self.screen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = (geo.width() - self.width()) // 2 + geo.x()
        y = (geo.height() - self.height()) // 2 + geo.y()
        self.move(x, y)
