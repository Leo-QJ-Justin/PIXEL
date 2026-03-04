# Desktop Pet

A modular desktop companion app. Supports pluggable **behaviors** (visual animations) and **integrations** (external service connections). Bring your own sprites!

## Features

- Transparent, draggable desktop pet that stays on top
- **Modular behavior system** - easily add new animations
- **Pluggable integrations** - connect to external services
- **Weather integration** - pet reacts to local weather (umbrella in rain, sunglasses in sun)
- **Google Calendar integration** - configurable event reminders with day preview
- **Pomodoro timer** - focus sessions with floating widget and pet reactions
- Animated sprites with idle, alert, wander, rainy, sunny, and time-of-day states
- Wandering behavior - pet randomly moves around your screen
- **Settings GUI** - MapleStory-themed dialog for all configuration
- System tray icon with integration controls

## Requirements

- Python 3.10+
- uv (Python package manager)

## Installation

1. Clone the repository and navigate to the project folder

2. Install dependencies with UV:
   ```bash
   uv sync
   ```

3. Add your sprites to the `behaviors/*/sprites/` directories (sprites are gitignored - each developer uses their own)

4. Configure your `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

5. Fill in the credentials for the integrations you want to use (see [Environment Variables](#environment-variables-env) below)

## Setup

Each integration requires its own one-time setup. Only set up the ones you plan to use.

### Weather

1. Get a free API key from [openweathermap.org](https://openweathermap.org/api)
2. Add `OPENWEATHER_API_KEY` to `.env`
3. Set your city in `settings.json` under `integrations.weather.city`

### Google Calendar

1. Create a project at [Google Cloud Console](https://console.cloud.google.com)
2. Enable the **Google Calendar API**
3. Create **OAuth client ID** credentials (Application type: Desktop app)
4. Add `GOOGLE_CALENDAR_CLIENT_ID` and `GOOGLE_CALENDAR_CLIENT_SECRET` to `.env`
5. Add your Gmail address as a test user under **OAuth consent screen** → **Test users**
6. Open **Settings → Calendar** in the app and click **Connect Google Calendar**

## Usage

Run the application:
```bash
uv run python main.py
```

### Running in Background (Windows)

To run the pet in the background:
```powershell
Start-Process '.venv\Scripts\pythonw.exe' -ArgumentList 'main.py' -WindowStyle Hidden
```

### Controls

- **Left-click + drag**: Move the pet around the screen
- **Left-click**: Dismiss alert
- **Right-click**: Open context menu (Reset Position, Settings, Quit)
- **System tray**: Double-click to show/hide, right-click for menu
- **Tray > Pomodoro**: Start/skip focus sessions, show timer widget
- **Tray > Calendar**: View next event, refresh calendar
- **Tray > Integrations**: Enable/disable other integrations

### Behavior

The pet will randomly wander around your screen. It reacts to:
- **Weather conditions** (umbrella sprite in rain, sunglasses in sun)
- **Calendar events** with configurable reminders:
  - *Day preview* on startup — "You have 3 meetings today. First is Standup at 9:30 AM."
  - *Countdown reminders* — speech bubble at 30 min and 5 min before
  - *Starting now* alert — pet alert behavior when event begins
  - All-day events mentioned in day preview only (no countdown)
- **Time of day** (morning, afternoon, night greetings)

## Configuration

### settings.json

```json
{
  "general": {
    "always_on_top": true,
    "start_minimized": false,
    "sprite_default_facing": "right",
    "speech_bubble": {
      "enabled": true,
      "duration_ms": 3000
    }
  },
  "behaviors": {
    "fly": {
      "wander_chance": 0.3,
      "wander_interval_min_ms": 5000,
      "wander_interval_max_ms": 15000
    }
  },
  "integrations": {
    "weather": {
      "enabled": true,
      "city": "New York",
      "units": "imperial",
      "check_interval_ms": 1800000
    },
    "google_calendar": {
      "enabled": false,
      "check_interval_ms": 300000,
      "calendar_id": "primary",
      "fetch_window_minutes": 120,
      "trigger_behavior": "alert",
      "reminder_minutes": [30, 5, 0],
      "day_preview_enabled": true
    },
    "pomodoro": {
      "enabled": true,
      "work_duration_minutes": 25,
      "short_break_minutes": 5,
      "long_break_minutes": 15,
      "auto_start": false,
      "sound_enabled": true,
      "sessions_per_cycle": 4
    }
  }
}
```

### Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENWEATHER_API_KEY` | For Weather | API key from [openweathermap.org](https://openweathermap.org/api) |
| `GOOGLE_CALENDAR_CLIENT_ID` | For Calendar | OAuth client ID from Google Cloud Console |
| `GOOGLE_CALENDAR_CLIENT_SECRET` | For Calendar | OAuth client secret |

## Project Structure

```
├── main.py                           # Entry point
├── config.py                         # Configuration loader
├── settings.json                     # Runtime config
├── .env                              # API credentials (never commit)
│
├── behaviors/                        # Visual animation states
│   ├── idle/
│   ├── alert/
│   ├── wander/
│   ├── wave/
│   ├── sleep/
│   ├── morning/
│   ├── night/
│   ├── rainy/
│   └── sunny/
│
├── integrations/                     # External service connections
│   ├── weather/
│   ├── pomodoro/
│   │   └── integration.py            # Focus timer logic
│   └── google_calendar/
│       ├── integration.py            # Reminder + day preview logic
│       ├── calendar_event.py         # Event model
│       └── auth.py                   # OAuth2 helpers
│
└── src/
    ├── core/
    │   ├── base_integration.py       # Abstract integration class
    │   ├── behavior_registry.py      # Behavior discovery & management
    │   └── integration_manager.py    # Integration lifecycle
    └── ui/
        ├── pet_window.py             # Desktop pet widget
        ├── dialog_box.py             # MapleStory-styled dialog boxes
        ├── speech_bubble.py          # Speech bubble overlay
        ├── settings_dialog.py        # Settings GUI (5 tabs)
        ├── pomodoro_widget.py        # Floating Pomodoro timer
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

3. Add sprite images in `sprites/` subfolder (e.g., `sleep_1.png`, `sleep_2.png`)

4. Optionally add sounds in `sounds/` subfolder

## Adding Custom Integrations

1. Create a folder in `integrations/` (e.g., `integrations/discord/`)

2. Create `integration.py` extending `BaseIntegration`

3. Add settings in `settings.json` under `integrations`

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
- **qasync** - Qt-asyncio integration
- **aiohttp** - Async HTTP client (API calls)
- **python-dotenv** - Environment variable management
- **google-api-python-client** - Google Calendar API
- **google-auth-oauthlib** - Google OAuth flow

## License

MIT
