"""Bridge between Python and JS for the React UI event bus."""

import json
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class BridgeHost(QObject):
    """Python side of the JS <-> Python event bus.

    Provides bidirectional event communication between the PyQt6 backend
    and a React frontend hosted in QWebEngineView via QWebChannel.
    """

    # Signal emitted toward JS; QWebChannel exposes this to the JS side
    eventDispatched = pyqtSignal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._handlers: defaultdict[str, list[Callable]] = defaultdict(list)
        self._js_callback: Callable[[str, str], None] | None = None

    # ------------------------------------------------------------------
    # JS -> Python
    # ------------------------------------------------------------------

    @pyqtSlot(str, str)
    def receive(self, event: str, payload_json: str) -> None:
        """Receive an event from JS and dispatch to registered Python handlers."""
        self._dispatch(event, payload_json)

    @pyqtSlot(str, str)
    def receiveFromJs(self, event: str, payload_json: str) -> None:
        """Alias for :meth:`receive` — matches the name the JS bridge calls."""
        self._dispatch(event, payload_json)

    def _dispatch(self, event: str, payload_json: str) -> None:
        """Parse JSON payload and dispatch to registered Python handlers."""
        try:
            data = json.loads(payload_json)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid JSON payload for event '%s': %s", event, payload_json)
            return

        for handler in self._handlers[event]:
            try:
                handler(data)
            except Exception:
                logger.exception("Exception in handler %s for event '%s'", handler, event)

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
        """Push an event from Python to the JS side via the signalEmitted signal."""
        payload_json = json.dumps(data)
        self.eventDispatched.emit(event, payload_json)
        if self._js_callback is not None:
            try:
                self._js_callback(event, payload_json)
            except Exception:
                logger.exception("Exception in JS callback for event '%s'", event)

    def register_js_callback(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback that receives all emitted events.

        Replaces any previously registered callback. Primarily used for
        testing to capture emitted events without a real QWebChannel.
        """
        self._js_callback = callback
