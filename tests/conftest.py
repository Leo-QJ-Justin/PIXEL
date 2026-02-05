"""Shared test fixtures for Haro Desktop Pet tests."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Minimal valid PNG (1x1 transparent pixel)
MINIMAL_PNG = bytes(
    [
        0x89,
        0x50,
        0x4E,
        0x47,
        0x0D,
        0x0A,
        0x1A,
        0x0A,  # PNG signature
        0x00,
        0x00,
        0x00,
        0x0D,
        0x49,
        0x48,
        0x44,
        0x52,  # IHDR chunk
        0x00,
        0x00,
        0x00,
        0x01,
        0x00,
        0x00,
        0x00,
        0x01,  # 1x1
        0x08,
        0x06,
        0x00,
        0x00,
        0x00,
        0x1F,
        0x15,
        0xC4,  # RGBA, etc
        0x89,
        0x00,
        0x00,
        0x00,
        0x0A,
        0x49,
        0x44,
        0x41,  # IDAT chunk
        0x54,
        0x78,
        0x9C,
        0x63,
        0x00,
        0x01,
        0x00,
        0x00,
        0x05,
        0x00,
        0x01,
        0x0D,
        0x0A,
        0x2D,
        0xB4,
        0x00,
        0x00,
        0x00,
        0x00,
        0x49,
        0x45,
        0x4E,
        0x44,
        0xAE,  # IEND chunk
        0x42,
        0x60,
        0x82,
    ]
)


@pytest.fixture
def temp_settings_file(tmp_path):
    """Create a temporary settings.json file with new nested structure."""
    settings_file = tmp_path / "settings.json"
    default_settings = {
        "general": {"always_on_top": True, "start_minimized": False},
        "behaviors": {},
        "integrations": {"telegram": {"enabled": True, "trigger_behavior": "alert"}},
    }
    settings_file.write_text(json.dumps(default_settings))
    return settings_file


@pytest.fixture
def temp_settings_with_users(tmp_path):
    """Create a temporary settings.json (users are now in .env, not here)."""
    settings_file = tmp_path / "settings.json"
    settings = {
        "general": {"always_on_top": True, "start_minimized": False},
        "behaviors": {"wander": {"wander_chance": 0.5}},
        "integrations": {"telegram": {"enabled": True, "trigger_behavior": "alert"}},
    }
    settings_file.write_text(json.dumps(settings))
    return settings_file


@pytest.fixture
def mock_behaviors_dir(tmp_path):
    """Create a temporary behaviors directory with idle, alert, and fly behaviors."""
    behaviors_dir = tmp_path / "behaviors"
    behaviors_dir.mkdir()

    # Create idle behavior
    idle_dir = behaviors_dir / "idle"
    idle_sprites = idle_dir / "sprites"
    idle_sprites.mkdir(parents=True)
    (idle_sprites / "idle_1.png").write_bytes(MINIMAL_PNG)
    (idle_sprites / "idle_2.png").write_bytes(MINIMAL_PNG)
    (idle_dir / "config.json").write_text(
        json.dumps(
            {
                "frame_duration_ms": 500,
                "loop": True,
                "priority": 0,
                "can_be_interrupted": True,
            }
        )
    )

    # Create alert behavior
    alert_dir = behaviors_dir / "alert"
    alert_sprites = alert_dir / "sprites"
    alert_sprites.mkdir(parents=True)
    (alert_sprites / "alert_1.png").write_bytes(MINIMAL_PNG)
    (alert_sprites / "alert_2.png").write_bytes(MINIMAL_PNG)
    (alert_dir / "config.json").write_text(
        json.dumps(
            {
                "frame_duration_ms": 300,
                "loop": False,
                "priority": 10,
                "can_be_interrupted": False,
            }
        )
    )

    # Create wander behavior
    wander_dir = behaviors_dir / "wander"
    wander_sprites = wander_dir / "sprites"
    wander_sprites.mkdir(parents=True)
    for i in range(1, 5):
        (wander_sprites / f"wander_{i}.png").write_bytes(MINIMAL_PNG)
    (wander_dir / "config.json").write_text(
        json.dumps(
            {
                "frame_duration_ms": 100,
                "loop": True,
                "priority": 5,
                "can_be_interrupted": True,
            }
        )
    )

    return behaviors_dir


@pytest.fixture
def mock_integrations_dir(tmp_path):
    """Create a temporary integrations directory."""
    integrations_dir = tmp_path / "integrations"
    integrations_dir.mkdir()
    return integrations_dir


@pytest.fixture
def behavior_registry(mock_behaviors_dir):
    """Create a BehaviorRegistry with mock behaviors loaded."""
    from src.core.behavior_registry import BehaviorRegistry

    registry = BehaviorRegistry()
    registry.discover_behaviors([mock_behaviors_dir])
    return registry


@pytest.fixture
def integration_manager(mock_integrations_dir, behavior_registry, temp_settings_file):
    """Create an IntegrationManager with mock paths."""
    from src.core.integration_manager import IntegrationManager

    with patch("config.SETTINGS_FILE", temp_settings_file):
        from config import load_settings

        settings = load_settings()

    manager = IntegrationManager(
        integrations_path=mock_integrations_dir,
        behavior_registry=behavior_registry,
        settings=settings,
    )
    return manager


@pytest.fixture
def mock_telegram_client():
    """Create a mocked TelegramClient."""
    client = MagicMock()
    client.start = AsyncMock()
    client.disconnect = AsyncMock()
    client.run_until_disconnected = AsyncMock()
    client.on = MagicMock(return_value=lambda f: f)
    return client


@pytest.fixture
def mock_env_with_users(monkeypatch):
    """Set up environment with monitored users."""
    monkeypatch.setenv("MONITORED_USERS", "123456789,987654321")
    monkeypatch.setenv("API_ID", "test_id")
    monkeypatch.setenv("API_HASH", "test_hash")


@pytest.fixture
def mock_env_empty_users(monkeypatch):
    """Set up environment with no monitored users."""
    monkeypatch.setenv("MONITORED_USERS", "")
    monkeypatch.setenv("API_ID", "test_id")
    monkeypatch.setenv("API_HASH", "test_hash")


# Legacy fixtures for backwards compatibility
@pytest.fixture
def mock_sprites_dir(tmp_path):
    """Create a temporary directory with minimal PNG files for testing."""
    sprites_dir = tmp_path / "sprites"
    sprites_dir.mkdir()

    for name in ["idle_1.png", "idle_2.png", "alert_1.png", "alert_2.png"]:
        (sprites_dir / name).write_bytes(MINIMAL_PNG)

    return sprites_dir


@pytest.fixture
def mock_sounds_dir(tmp_path):
    """Create a temporary directory for sounds."""
    sounds_dir = tmp_path / "sounds"
    sounds_dir.mkdir()
    return sounds_dir
