import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenWeatherMap API key
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Google Calendar OAuth credentials (optional override — bundled defaults in auth.py)
GOOGLE_CALENDAR_CLIENT_ID = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
GOOGLE_CALENDAR_CLIENT_SECRET = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")

# Project paths
BASE_DIR = Path(__file__).parent
BEHAVIORS_DIR = BASE_DIR / "behaviors"
INTEGRATIONS_DIR = BASE_DIR / "integrations"

# Settings file path
SETTINGS_FILE = BASE_DIR / "settings.json"

# Default settings structure
DEFAULT_SETTINGS = {
    "user_name": "",
    "birthday": "",
    "general": {
        "always_on_top": True,
        "start_minimized": False,
        "start_on_boot": False,
        "sprite_default_facing": "right",  # "left" or "right"
        "speech_bubble": {
            "enabled": True,
            "duration_ms": 3000,
        },
    },
    "behaviors": {
        "wander": {
            "wander_chance": 0.3,
            "wander_interval_min_ms": 5000,
            "wander_interval_max_ms": 15000,
        },
        "wave": {
            "greeting": "Hello!",
        },
        "idle_variety": {
            "enabled": True,
            "interval_min_ms": 20000,
            "interval_max_ms": 60000,
            "chance": 0.4,
            "behaviors": ["look_around", "yawn", "chill", "play_ball", "crochet"],
        },
        "sleep": {
            "inactivity_timeout_ms": 60000,
            "schedule_enabled": False,
            "schedule_start": "22:00",
            "schedule_end": "06:00",
        },
        "time_periods": {
            "enabled": True,
            "check_interval_ms": 30000,
            "periods": {
                "morning": "06:00",
                "afternoon": "12:00",
                "night": "20:00",
            },
            "greetings": {
                "morning": "Rise and shine!",
                "afternoon": "Lunch time~",
                "night": "Sleepy time~",
            },
        },
    },
    "personality_engine": {
        "enabled": False,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key": "",
        "endpoint": "",
    },
    "integrations": {
        "pomodoro": {
            "enabled": True,
            "work_duration_minutes": 25,
            "short_break_minutes": 5,
            "long_break_minutes": 15,
            "auto_start": False,
            "sound_enabled": True,
            "sessions_per_cycle": 4,
        },
        "encouraging": {
            "enabled": True,
            "cooldown_min_minutes": 30,
            "cooldown_max_minutes": 60,
            "evaluation_interval_seconds": 30,
            "triggers": {
                "restless": {"enabled": True, "threshold_minutes": 90},
                "observant": {"enabled": True},
                "excited": {"enabled": True, "idle_threshold_minutes": 15},
                "proud": {"enabled": True, "streak_threshold": 3},
                "curious": {"enabled": True},
                "impressed": {"enabled": True, "milestone_interval": 10},
            },
        },
        "google_calendar": {
            "enabled": False,
            "check_interval_ms": 300000,
            "calendar_id": "primary",
            "fetch_window_minutes": 120,
            "trigger_behavior": "alert",
            "reminder_minutes": [30, 5, 0],
            "day_preview_enabled": True,
        },
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


def get_sprite_default_facing() -> str:
    """Get the default facing direction for sprites ('left' or 'right')."""
    settings = load_settings()
    return settings.get("general", {}).get("sprite_default_facing", "right")
