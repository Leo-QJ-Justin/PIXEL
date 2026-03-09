"""Shared test fixtures for desktop pet tests."""

import json
from unittest.mock import patch

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
        "integrations": {"weather": {"enabled": True, "trigger_behavior": "alert"}},
    }
    settings_file.write_text(json.dumps(default_settings))
    return settings_file


@pytest.fixture
def temp_settings_with_users(tmp_path):
    """Create a temporary settings.json with behaviors."""
    settings_file = tmp_path / "settings.json"
    settings = {
        "general": {"always_on_top": True, "start_minimized": False},
        "behaviors": {"wander": {"wander_chance": 0.5}},
        "integrations": {"weather": {"enabled": True, "trigger_behavior": "alert"}},
    }
    settings_file.write_text(json.dumps(settings))
    return settings_file


@pytest.fixture
def mock_behaviors_dir(tmp_path):
    """Create a temporary behaviors directory with idle, wander, and other behaviors."""
    behaviors_dir = tmp_path / "behaviors"
    behaviors_dir.mkdir()

    # Create idle behavior
    idle_dir = behaviors_dir / "idle"
    idle_media = idle_dir / "media"
    idle_media.mkdir(parents=True)
    (idle_media / "idle_1.png").write_bytes(MINIMAL_PNG)
    (idle_media / "idle_2.png").write_bytes(MINIMAL_PNG)
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

    # Create wander behavior
    wander_dir = behaviors_dir / "wander"
    wander_media = wander_dir / "media"
    wander_media.mkdir(parents=True)
    for i in range(1, 5):
        (wander_media / f"wander_{i}.png").write_bytes(MINIMAL_PNG)
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

    # Create wave behavior
    wave_dir = behaviors_dir / "wave"
    wave_media = wave_dir / "media"
    wave_media.mkdir(parents=True)
    (wave_media / "wave_1.png").write_bytes(MINIMAL_PNG)
    (wave_media / "wave_2.png").write_bytes(MINIMAL_PNG)
    (wave_dir / "config.json").write_text(
        json.dumps(
            {
                "frame_duration_ms": 400,
                "loop": False,
                "priority": 3,
                "can_be_interrupted": True,
            }
        )
    )

    # Create flinch behavior (click reaction)
    flinch_dir = behaviors_dir / "flinch"
    flinch_media = flinch_dir / "media"
    flinch_media.mkdir(parents=True)
    (flinch_media / "flinch_1.png").write_bytes(MINIMAL_PNG)
    (flinch_media / "flinch_2.png").write_bytes(MINIMAL_PNG)
    (flinch_dir / "config.json").write_text(
        json.dumps(
            {
                "frame_duration_ms": 150,
                "loop": False,
                "priority": 4,
                "can_be_interrupted": True,
            }
        )
    )

    # Create look_around behavior (idle variety)
    look_dir = behaviors_dir / "look_around"
    look_media = look_dir / "media"
    look_media.mkdir(parents=True)
    (look_media / "look_around_1.png").write_bytes(MINIMAL_PNG)
    (look_media / "look_around_2.png").write_bytes(MINIMAL_PNG)
    (look_dir / "config.json").write_text(
        json.dumps(
            {
                "frame_duration_ms": 300,
                "loop": False,
                "priority": 1,
                "can_be_interrupted": True,
            }
        )
    )

    # Create yawn behavior (idle variety)
    yawn_dir = behaviors_dir / "yawn"
    yawn_media = yawn_dir / "media"
    yawn_media.mkdir(parents=True)
    (yawn_media / "yawn_1.png").write_bytes(MINIMAL_PNG)
    (yawn_media / "yawn_2.png").write_bytes(MINIMAL_PNG)
    (yawn_dir / "config.json").write_text(
        json.dumps(
            {
                "frame_duration_ms": 400,
                "loop": False,
                "priority": 1,
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


# Legacy fixtures for backwards compatibility
@pytest.fixture
def mock_media_dir(tmp_path):
    """Create a temporary directory with minimal PNG files for testing."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()

    for name in ["idle_1.png", "idle_2.png"]:
        (media_dir / name).write_bytes(MINIMAL_PNG)

    return media_dir


@pytest.fixture
def mock_sounds_dir(tmp_path):
    """Create a temporary directory for sounds."""
    sounds_dir = tmp_path / "sounds"
    sounds_dir.mkdir()
    return sounds_dir
