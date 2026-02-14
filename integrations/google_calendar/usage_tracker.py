"""API usage tracker — file-based quota counter with monthly reset."""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path

from config import BASE_DIR

logger = logging.getLogger(__name__)

_USAGE_FILE = BASE_DIR / "api_usage.json"


class UsageTracker:
    """Tracks API call counts to stay within free-tier limits.

    Persists to api_usage.json in the project root. Resets monthly.
    Thread-safe via threading.Lock.
    """

    def __init__(self, usage_file: Path | None = None, quota_limit: int = 9500) -> None:
        self._file = usage_file or _USAGE_FILE
        self._limit = quota_limit
        self._lock = threading.Lock()
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        """Load usage data from file, resetting if month has changed."""
        with self._lock:
            if self._file.exists():
                try:
                    with open(self._file) as f:
                        self._data = json.load(f)
                except (json.JSONDecodeError, OSError):
                    logger.warning("Corrupted api_usage.json, resetting")
                    self._data = {}
            else:
                self._data = {}

            self._check_month_reset()

    def _save(self) -> None:
        """Save usage data to file (must be called with lock held)."""
        try:
            with open(self._file, "w") as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            logger.exception("Failed to save api_usage.json")

    def _check_month_reset(self) -> None:
        """Reset counters if the month has changed (must be called with lock held)."""
        current_month = datetime.now().strftime("%Y-%m")
        if self._data.get("month") != current_month:
            logger.info(f"API usage month reset: {self._data.get('month')} -> {current_month}")
            self._data = {"month": current_month}
            self._save()

    def can_call(self, api_name: str) -> bool:
        """Check if an API call is within quota."""
        with self._lock:
            self._check_month_reset()
            count = self._data.get(api_name, 0)
            return count < self._limit

    def increment(self, api_name: str) -> None:
        """Record an API call. Saves immediately (edge case #10)."""
        with self._lock:
            self._check_month_reset()
            self._data[api_name] = self._data.get(api_name, 0) + 1
            self._save()

    def get_usage(self) -> dict:
        """Return current usage counts for display."""
        with self._lock:
            self._check_month_reset()
            return {
                "month": self._data.get("month", ""),
                "routes_api": self._data.get("routes_api", 0),
                "geocoding_api": self._data.get("geocoding_api", 0),
                "limit": self._limit,
            }
