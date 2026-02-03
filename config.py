import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Project paths
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
SOUNDS_DIR = ASSETS_DIR / "sounds"

# Settings file path
SETTINGS_FILE = BASE_DIR / "settings.json"


def load_settings() -> dict:
    """Load settings from JSON file."""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"monitored_users": []}


def save_settings(settings: dict) -> None:
    """Save settings to JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def get_monitored_users() -> list:
    """Get list of monitored Telegram user IDs."""
    settings = load_settings()
    return settings.get("monitored_users", [])


def add_monitored_user(user_id: int) -> None:
    """Add a user ID to the monitored list."""
    settings = load_settings()
    if user_id not in settings["monitored_users"]:
        settings["monitored_users"].append(user_id)
        save_settings(settings)


def remove_monitored_user(user_id: int) -> None:
    """Remove a user ID from the monitored list."""
    settings = load_settings()
    if user_id in settings["monitored_users"]:
        settings["monitored_users"].remove(user_id)
        save_settings(settings)
