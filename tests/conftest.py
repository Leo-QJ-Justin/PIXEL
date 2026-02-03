"""Shared test fixtures for Haro Desktop Pet tests."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def temp_settings_file(tmp_path):
    """Create a temporary settings.json file."""
    settings_file = tmp_path / "settings.json"
    default_settings = {"monitored_users": []}
    settings_file.write_text(json.dumps(default_settings))
    return settings_file


@pytest.fixture
def temp_settings_with_users(tmp_path):
    """Create a temporary settings.json with some monitored users."""
    settings_file = tmp_path / "settings.json"
    settings = {"monitored_users": [123456789, 987654321]}
    settings_file.write_text(json.dumps(settings))
    return settings_file


@pytest.fixture
def mock_sprites_dir(tmp_path):
    """Create a temporary directory with minimal PNG files for testing."""
    sprites_dir = tmp_path / "sprites"
    sprites_dir.mkdir()

    # Create minimal valid PNG files (1x1 transparent pixel)
    # PNG header + IHDR + IDAT + IEND chunks for 1x1 RGBA image
    minimal_png = bytes(
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

    # Create idle and alert sprites
    for name in ["idle_1.png", "idle_2.png", "alert_1.png", "alert_2.png"]:
        (sprites_dir / name).write_bytes(minimal_png)

    return sprites_dir


@pytest.fixture
def mock_sounds_dir(tmp_path):
    """Create a temporary directory for sounds."""
    sounds_dir = tmp_path / "sounds"
    sounds_dir.mkdir()
    return sounds_dir


@pytest.fixture
def mock_telegram_client():
    """Create a mocked TelegramClient."""
    client = MagicMock()
    client.start = AsyncMock()
    client.disconnect = AsyncMock()
    client.run_until_disconnected = AsyncMock()
    client.on = MagicMock(return_value=lambda f: f)
    return client
