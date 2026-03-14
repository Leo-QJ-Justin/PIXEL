"""Bridge between Python and JS for the React UI event bus."""

import json
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QObject, pyqtSlot

logger = logging.getLogger(__name__)


class BridgeHost(QObject):
    """Python side of the JS <-> Python event bus.

    Provides bidirectional event communication between the PyQt6 backend
    and a React frontend hosted in QWebEngineView via QWebChannel.
    """

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._handlers: defaultdict[str, list[Callable]] = defaultdict(list)
        self._js_callback: Callable[[str, str], None] | None = None

    # ------------------------------------------------------------------
    # JS -> Python
    # ------------------------------------------------------------------

    @pyqtSlot(str, str)
    def receive(self, event: str, payload_json: str) -> None:
        """Receive an event from JS and dispatch to registered Python handlers.

        Called by the JS side via QWebChannel.  *payload_json* is parsed as
        JSON before being passed to handlers.  Invalid JSON is logged as a
        warning and silently ignored.
        """
        try:
            data = json.loads(payload_json)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid JSON payload for event '%s': %s", event, payload_json)
            return

        for handler in self._handlers[event]:
            try:
                handler(data)
            except Exception:
                logger.exception(
                    "Exception in handler %s for event '%s'", handler, event
                )

    def on(self, event: str, handler: Callable[[Any], None]) -> None:
        """Register a Python handler for *event*.

        Multiple handlers per event are supported; they are called in
        registration order.
        """
        self._handlers[event].append(handler)

    # ------------------------------------------------------------------
    # Python -> JS
    # ------------------------------------------------------------------

    def emit(self, event: str, data: Any = None) -> None:
        """Push an event from Python to the JS side.

        If no JS callback has been registered yet the call is a silent
        no-op so that Python code can emit events before the webview is
        ready without crashing.
        """
        if self._js_callback is None:
            logger.debug("emit('%s') called but no JS callback registered yet", event)
            return

        payload_json = json.dumps(data)
        try:
            self._js_callback(event, payload_json)
        except Exception:
            logger.exception("Exception calling JS callback for event '%s'", event)

    def register_js_callback(self, callback: Callable[[str, str], None]) -> None:
        """Register the JS-side callback used by :meth:`emit`.

        This is called once by :class:`PanelHost` after the web channel is
        set up.
        """
        self._js_callback = callback
