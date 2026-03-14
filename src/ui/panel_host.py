"""Panel host window that embeds the React UI in a QWebEngineView."""

import logging
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWebChannel import QWebChannel
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
        self.resize(600, 750)
        self.setMinimumSize(450, 500)

    def _setup_web_view(self) -> None:
        """Create the QWebEngineView and set it as central widget."""
        self._view = QWebEngineView(self)
        self.setCentralWidget(self._view)

    def _setup_channel(self) -> None:
        """Wire up QWebChannel so the JS side can talk to BridgeHost."""
        self._channel = QWebChannel(self._view.page())
        self._channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(self._channel)

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
        """Show the window, raise it, and emit a ``panel.open`` event."""
        self.show()
        self.raise_()
        self._center_on_screen()
        self._bridge.emit("panel.open", {"panel": panel})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        """Center the window on the current screen."""
        screen = self.screen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = (geo.width() - self.width()) // 2 + geo.x()
        y = (geo.height() - self.height()) // 2 + geo.y()
        self.move(x, y)
