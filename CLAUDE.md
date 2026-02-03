# Haro Desktop Pet

A modular desktop companion application featuring Haro from Gundam SEED. Supports pluggable **behaviors** (visual animations) and **integrations** (external service connections like Telegram, Discord, weather, etc.).

## Tech Stack

- **Python 3.10+**
- **PyQt6** - Desktop GUI with transparency and animations
- **Telethon** - Async Telegram MTProto client
- **qasync** - Qt/asyncio event loop integration
- **python-dotenv** - Environment variable management
- **uv** - Package manager

## Project Structure

```
├── main.py                           # Entry point
├── config.py                         # Configuration loader
├── settings.json                     # Runtime config (behaviors, integrations)
├── .env                              # API credentials (NEVER COMMIT)
│
├── scripts/                          # Utility scripts
│   ├── auth_telegram.py              # Telegram authentication helper
│   └── debug_telegram.py             # Telegram debugging/testing
│
├── behaviors/                        # Core behaviors (visual states)
│   ├── idle/
│   │   ├── config.json               # Animation config
│   │   └── sprites/
│   ├── alert/
│   │   ├── config.json
│   │   ├── sprites/
│   │   └── sounds/
│   └── fly/
│       ├── config.json
│       └── sprites/
│
├── integrations/                     # External service connections
│   ├── telegram/
│   │   ├── integration.py            # TelegramIntegration class
│   │   └── README.md
│   ├── discord/                      # (example)
│   │   ├── integration.py
│   │   └── behaviors/                # Integration-specific behaviors
│   │       └── mention/
│   └── weather/                      # (example)
│       ├── integration.py
│       └── behaviors/
│           ├── rain/
│           └── sunny/
│
└── src/
    ├── core/
    │   ├── base_integration.py       # Abstract integration class
    │   ├── behavior_registry.py      # Discovers & manages behaviors
    │   └── integration_manager.py    # Discovers & manages integrations
    └── ui/
        ├── haro_window.py            # Renders current behavior
        └── tray_icon.py              # System tray integration
```

## Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py

# Run in background (Windows, hides terminal)
Start-Process '.venv\Scripts\pythonw.exe' -ArgumentList 'main.py' -WindowStyle Hidden

# Test Telegram authentication
uv run python scripts/auth_telegram.py

# Debug Telegram messages (shows sender IDs)
uv run python scripts/debug_telegram.py
```

## First-Time Setup

1. Get API credentials from https://my.telegram.org
2. Create `.env` file with `API_ID` and `API_HASH`
3. Run the app and authenticate with phone + verification code
4. Session is cached in `haro_session.session`

## Architecture

### Core Concepts

| Concept | What It Is | What It Owns |
|---------|-----------|--------------|
| **Behaviors** | Visual/animation states of Haro | Sprites, sounds, animation timing |
| **Integrations** | External service connections | API logic, decides when to trigger behaviors |

**Relationship:** Integrations trigger Behaviors

```
Telegram message → TelegramIntegration → triggers "alert" → BehaviorRegistry plays alert sprites
```

### Key Components

- **BehaviorRegistry**: Discovers behaviors from `behaviors/` and `integrations/*/behaviors/`, manages priority-based behavior switching
- **IntegrationManager**: Discovers and manages integration lifecycle (start/stop), connects integration signals to BehaviorRegistry
- **BaseIntegration**: Abstract class that all integrations extend
- **HaroWidget**: Frameless transparent window, renders sprites from current behavior

### Signal Flow

```
Integration.request_behavior → IntegrationManager → BehaviorRegistry.trigger → HaroWidget updates
```

---

## Adding a New Behavior

1. Create a folder in `behaviors/` (e.g., `behaviors/sleep/`)

2. Add `config.json`:
```json
{
  "frame_duration_ms": 500,
  "loop": true,
  "priority": 2,
  "sound": null,
  "can_be_interrupted": true
}
```

| Field | Description |
|-------|-------------|
| `frame_duration_ms` | Milliseconds per animation frame |
| `loop` | Whether animation repeats |
| `priority` | Higher priority interrupts lower (idle=0, fly=5, alert=10) |
| `sound` | Sound file in `sounds/` subfolder (optional) |
| `can_be_interrupted` | Whether other behaviors can interrupt this one |

3. Add sprites in `sprites/` subfolder (e.g., `sleep_1.png`, `sleep_2.png`)

4. Optionally add sounds in `sounds/` subfolder

---

## Adding a New Integration

1. Create a folder in `integrations/` (e.g., `integrations/discord/`)

2. Create `integration.py` extending `BaseIntegration`:

```python
from src.core.base_integration import BaseIntegration

class DiscordIntegration(BaseIntegration):
    @property
    def name(self) -> str:
        return "discord"

    @property
    def display_name(self) -> str:
        return "Discord Notifications"

    def get_default_settings(self) -> dict:
        return {
            "enabled": False,
            "trigger_behavior": "alert"
        }

    async def start(self) -> None:
        # Connect to service, set up listeners
        # Call self.trigger("behavior_name", context) when events occur
        pass

    async def stop(self) -> None:
        # Clean up connections
        pass
```

3. Add settings in `settings.json`:
```json
{
  "integrations": {
    "discord": {
      "enabled": true,
      "trigger_behavior": "alert"
    }
  }
}
```

4. Optionally add custom behaviors in `integrations/discord/behaviors/`

---

## Settings Structure

### settings.json
```json
{
  "general": {
    "always_on_top": true,
    "start_minimized": false
  },
  "behaviors": {
    "fly": {
      "wander_chance": 0.3,
      "wander_interval_min_ms": 5000,
      "wander_interval_max_ms": 15000
    }
  },
  "integrations": {
    "telegram": {
      "enabled": true,
      "trigger_behavior": "alert"
    }
  }
}
```

### .env (sensitive data - never commit)
```bash
API_ID=your_api_id_here
API_HASH=your_api_hash_here
MONITORED_USERS=123456789,987654321
```

---

## SECURITY GUARDRAILS

### Sensitive Files - NEVER Commit

These files contain secrets and must remain local:

- `.env` - Contains `API_ID` and `API_HASH`
- `*.session` - Telegram authentication session tokens
- `*.session-journal` - Session transaction logs

### When Testing or Debugging

**DO NOT:**
- Print, log, or display `API_ID` or `API_HASH` values
- Include credentials in error messages or stack traces
- Create test files that contain hardcoded credentials
- Copy `.env` contents into any other file
- Use actual API credentials in example code or documentation

**DO:**
- Use placeholder values in examples: `API_ID="your_api_id_here"`
- Verify `.env` is in `.gitignore` before any git operations
- Check `git status` before committing to ensure no secrets are staged
- Use environment variable checks that don't expose values:
  ```python
  # Good - checks existence without exposing value
  if not os.getenv("API_ID"):
      print("Error: API_ID not configured")

  # Bad - exposes the actual value
  print(f"Using API_ID: {os.getenv('API_ID')}")
  ```

### Before Any Git Commit

1. Run `git status` to review staged files
2. Ensure `.env` and `*.session` files are NOT listed
3. If accidentally staged, run: `git reset HEAD .env`
4. Verify `.gitignore` contains:
   ```
   .env
   *.session
   *.session-journal
   ```
