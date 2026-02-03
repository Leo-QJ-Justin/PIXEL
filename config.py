import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Monitored users (comma-separated list in .env)
# Example: MONITORED_USERS=123456789,987654321
_monitored_users_str = os.getenv("MONITORED_USERS", "")
MONITORED_USERS = [
    int(uid.strip()) for uid in _monitored_users_str.split(",") if uid.strip().isdigit()
]

# Project paths
BASE_DIR = Path(__file__).parent
BEHAVIORS_DIR = BASE_DIR / "behaviors"
INTEGRATIONS_DIR = BASE_DIR / "integrations"

# Legacy paths (for backwards compatibility during transition)
ASSETS_DIR = BASE_DIR / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
SOUNDS_DIR = ASSETS_DIR / "sounds"

# Settings file path
SETTINGS_FILE = BASE_DIR / "settings.json"

# Default settings structure
DEFAULT_SETTINGS = {
    "general": {
        "always_on_top": True,
        "start_minimized": False,
    },
    "behaviors": {
        "fly": {
            "wander_chance": 0.3,
            "wander_interval_min_ms": 5000,
            "wander_interval_max_ms": 15000,
        }
    },
    "integrations": {
        "telegram": {
            "enabled": True,
            "trigger_behavior": "alert",
        }
    },
}


def load_settings() -> dict:
    """Load settings from JSON file, merging with defaults."""
    import copy

    settings = copy.deepcopy(DEFAULT_SETTINGS)

    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE) as f:
            file_settings = json.load(f)
            # Deep merge file settings into defaults
            _deep_merge(settings, file_settings)

    return settings


def save_settings(settings: dict) -> None:
    """Save settings to JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def _deep_merge(base: dict, override: dict) -> None:
    """Deep merge override into base dict, modifying base in place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def get_monitored_users() -> list[int]:
    """Get list of monitored Telegram user IDs from environment."""
    return MONITORED_USERS.copy()


def get_integration_settings(name: str) -> dict:
    """Get settings for a specific integration."""
    settings = load_settings()
    return settings.get("integrations", {}).get(name, {})


def get_behavior_settings(name: str) -> dict:
    """Get settings for a specific behavior."""
    settings = load_settings()
    return settings.get("behaviors", {}).get(name, {})


def get_general_settings() -> dict:
    """Get general application settings."""
    settings = load_settings()
    return settings.get("general", {})
