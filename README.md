# Haro Desktop Pet

A modular desktop companion app featuring Haro from Gundam SEED. Supports pluggable **behaviors** (visual animations) and **integrations** (external service connections like Telegram).

## Features

- Transparent, draggable desktop pet that stays on top
- **Modular behavior system** - easily add new animations
- **Pluggable integrations** - connect to external services
- Telegram integration to monitor messages from VIP contacts
- Visual and audio alerts when monitored users send messages
- Animated sprites with idle, alert, and wander states
- Wandering behavior - Haro randomly wanders around your screen
- System tray icon with integration controls

## Requirements

- Python 3.10+
- uv (Python package manager)
- Telegram API credentials (for Telegram integration)

## Installation

1. Clone the repository and navigate to the project folder

2. Install dependencies with UV:
   ```bash
   uv sync
   ```

3. Get your Telegram API credentials from [my.telegram.org](https://my.telegram.org)

4. Configure your `.env` file:
   ```bash
   # Telegram API credentials
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here

   # Monitored Telegram user IDs (comma-separated)
   MONITORED_USERS=123456789,987654321
   ```

   To find a user's ID, forward a message from them to [@userinfobot](https://t.me/userinfobot).

## Usage

Run the application:
```bash
uv run python main.py
```

### First Run Authentication

On first run, Telegram will prompt you in the terminal to:
1. Enter your phone number (with country code, e.g., +1234567890)
2. Enter the verification code sent to your Telegram app
3. Enter your 2FA password (if enabled)

This only happens once - the session is saved to `haro_session.session` and reused on subsequent runs.

### Running in Background (Windows)

To run Haro in the background:
```powershell
Start-Process '.venv\Scripts\pythonw.exe' -ArgumentList 'main.py' -WindowStyle Hidden
```

### Controls

- **Left-click + drag**: Move Haro around the screen
- **Left-click**: Dismiss alert
- **Right-click**: Open context menu (Reset Position, Quit)
- **System tray**: Double-click to show/hide, right-click for menu
- **Tray > Integrations**: Enable/disable integrations

### Behavior

Haro will randomly wander around your screen, moving left or right every few seconds. When a monitored user sends a Telegram message, Haro will bounce and play an alert sound until you click to dismiss.

## Configuration

### settings.json

```json
{
  "general": {
    "always_on_top": true,
    "start_minimized": false
  },
  "behaviors": {
    "wander": {
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

### Environment Variables (.env)

| Variable | Description |
|----------|-------------|
| `API_ID` | Telegram API ID from my.telegram.org |
| `API_HASH` | Telegram API Hash from my.telegram.org |
| `MONITORED_USERS` | Comma-separated list of Telegram user IDs to monitor |

## Project Structure

```
├── main.py                           # Entry point
├── config.py                         # Configuration loader
├── settings.json                     # Runtime config
├── .env                              # API credentials (never commit)
│
├── behaviors/                        # Visual animation states
│   ├── idle/
│   │   ├── config.json
│   │   └── sprites/
│   ├── alert/
│   │   ├── config.json
│   │   ├── sprites/
│   │   └── sounds/
│   └── wander/
│       ├── config.json
│       └── sprites/
│
├── integrations/                     # External service connections
│   └── telegram/
│       ├── integration.py
│       └── README.md
│
└── src/
    ├── core/
    │   ├── base_integration.py       # Abstract integration class
    │   ├── behavior_registry.py      # Behavior discovery & management
    │   └── integration_manager.py    # Integration lifecycle
    └── ui/
        ├── haro_window.py            # Desktop pet widget
        └── tray_icon.py              # System tray icon
```

## Adding Custom Behaviors

1. Create a folder in `behaviors/` (e.g., `behaviors/sleep/`)

2. Add `config.json`:
   ```json
   {
     "frame_duration_ms": 500,
     "loop": true,
     "priority": 2,
     "can_be_interrupted": true
   }
   ```

3. Add sprite images in `sprites/` subfolder

4. Optionally add sounds in `sounds/` subfolder

See [CLAUDE.md](CLAUDE.md) for detailed documentation.

## Adding Custom Integrations

1. Create a folder in `integrations/` (e.g., `integrations/discord/`)

2. Create `integration.py` extending `BaseIntegration`

3. Add settings in `settings.json` under `integrations`

See [CLAUDE.md](CLAUDE.md) for detailed documentation and examples.

## Development

### Running Tests

```bash
uv run pytest tests/ -v
```

### Code Style

```bash
uv run ruff check .
uv run ruff format .
```

## Dependencies

- **PyQt6** - GUI framework
- **Telethon** - Telegram client library
- **qasync** - Qt-asyncio integration
- **python-dotenv** - Environment variable management

## License

MIT
