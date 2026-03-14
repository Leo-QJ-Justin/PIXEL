# PIXEL

**P**ersonal **I**nteractive e**X**tensible **E**veryday **L**ife companion — a modular desktop pet with pluggable **behaviors** (visual animations) and **integrations** (external service connections). Bring your own sprites!

## Features

- Transparent, draggable desktop pet that stays on top
- **Modular behavior system** - easily add new animations
- **Pluggable integrations** - connect to external services
- **Weather integration** - pet reacts to local weather (umbrella in rain, sunglasses in sun)
- **Google Calendar integration** - configurable event reminders with day preview
- **Pomodoro timer** - focus sessions with floating widget and pet reactions
- **Journal integration** - privacy-first daily journaling with mood tracking, calendar heat map, and LLM text cleanup
- **Birthday celebration** - set your birthday and the pet celebrates on the day (SGT)
- **MapleStory-style UI** - 9-slice sprite-based dialog boxes and speech bubbles
- Animated sprites with idle, wander, rainy, and time-of-day states
- Wandering behavior - pet randomly moves around your screen
- **AI personality engine** - optional LLM-powered speech rewriting (OpenAI, OpenRouter, Ollama)
- **Settings GUI** - claymorphism-themed dialog for all configuration
- System tray icon with integration controls

## Requirements

- Python 3.10+
- uv (Python package manager)
- Node.js 18+ and npm (for the React UI)
- System libraries for WebEngine (Linux/WSL): `sudo apt install libnss3 libasound2t64` (or `libasound2` on older Ubuntu)

## Installation

### Quick Setup

```bash
./setup.sh
```

This checks prerequisites, installs all dependencies, builds the React UI, and creates your `.env` file. Works on Linux, macOS, and WSL.

### Manual Setup

1. Clone the repository and navigate to the project folder

2. Install Python dependencies:
   ```bash
   uv sync
   ```

3. Install and build the React UI:
   ```bash
   cd ui
   npm install
   npm run build
   cd ..
   ```

4. (Linux/WSL) Install system libraries for WebEngine:
   ```bash
   sudo apt install libnss3 libasound2t64  # or libasound2 on older Ubuntu
   ```

5. Add your sprites to the `behaviors/*/media/` directories (sprites are gitignored - each developer uses their own)

6. Configure your `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

7. Fill in the credentials for the integrations you want to use (see [Environment Variables](#environment-variables-env) below)

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

### React UI Development Mode

To develop the React UI with hot-reload:
```bash
# Terminal 1: Start Vite dev server
cd ui && npm run dev

# Terminal 2: Start app in dev mode (loads UI from Vite instead of built files)
PIXEL_DEV_UI=1 uv run python main.py
```

### Running in Background (Windows)

To run the pet in the background:
```powershell
Start-Process '.venv\Scripts\pythonw.exe' -ArgumentList 'main.py' -WindowStyle Hidden
```

### Controls

- **Left-click + drag**: Move the pet around the screen
- **Left-click**: Tap reaction
- **Right-click**: Open context menu (Reset Position, Settings, Quit)
- **System tray**: Double-click to show/hide, right-click for menu
- **Tray > Behaviors**: Manually trigger any loaded behavior
- **Tray > Pomodoro**: Start/skip focus sessions, show timer widget
- **Tray > Calendar**: View next event, refresh calendar
- **Tray > Integrations**: Enable/disable other integrations

### Behavior

The pet will randomly wander around your screen. It reacts to:
- **Weather conditions** (umbrella sprite in rain, sunglasses in sun)
- **Calendar events** with configurable reminders:
  - *Day preview* on startup — "You have 3 meetings today. First is Standup at 9:30 AM."
  - *Countdown reminders* — speech bubble at 30 min and 5 min before
  - *Starting now* — pet reacts when event begins
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
  "personality_engine": {
    "enabled": false,
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "",
    "endpoint": ""
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
    },
    "journal": {
      "enabled": true,
      "nudge_frequency": "smart",
      "nudge_time": "20:00",
      "blur_on_focus_loss": true
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
| `LLM_API_KEY` | No | Override personality engine API key (takes precedence over Settings UI) |
| `LLM_ENDPOINT` | No | Override personality engine endpoint (e.g. for Ollama) |

## Project Structure

```
├── main.py                           # Entry point
├── config.py                         # Configuration loader
├── settings.json                     # Runtime config
├── .env                              # API credentials (never commit)
│
├── assets/                           # UI sprite assets
│   ├── dialog_frame.png              # 9-slice dialog frame
│   ├── speech_bubble.png             # 9-slice speech bubble
│   ├── button_yellow.png             # Accept button sprite
│   ├── button_pink.png               # Reject button sprite
│   └── fonts/                        # Custom fonts
│
├── behaviors/                        # Visual animation states
│   ├── idle/
│   ├── wander/
│   ├── wave/
│   ├── sleep/
│   └── ...
│
├── integrations/                     # External service connections
│   ├── weather/
│   ├── pomodoro/
│   │   └── integration.py            # Focus timer logic
│   ├── journal/
│   │   ├── integration.py            # Nudge timer & mood reactions
│   │   └── store.py                  # SQLite journal storage
│   └── google_calendar/
│       ├── integration.py            # Reminder + day preview logic
│       ├── calendar_event.py         # Event model
│       └── auth.py                   # OAuth2 helpers
│
├── ui/                               # React panel app (Vite + TypeScript)
│   ├── src/
│   │   ├── bridge/                   # Typed event bus (QWebChannel + mock)
│   │   ├── pages/
│   │   │   ├── journal/              # Stats, vault, editor, calendar map
│   │   │   ├── settings/             # 4-tab settings (General, Behaviors, etc.)
│   │   │   └── pomodoro/             # Timer, progress ring, stats
│   │   ├── components/ui/            # shadcn/ui components
│   │   └── App.tsx                   # Router + BridgeProvider
│   ├── package.json
│   └── vite.config.ts
│
└── src/
    ├── core/
    │   ├── base_integration.py       # Abstract integration class
    │   ├── behavior_registry.py      # Behavior discovery & management
    │   ├── integration_manager.py    # Integration lifecycle
    │   └── pet_state.py              # Pet state machine
    └── ui/
        ├── pet_window.py             # Desktop pet widget (native PyQt6)
        ├── dialog_box.py             # MapleStory-styled dialog boxes
        ├── speech_bubble.py          # 9-slice speech bubble overlay
        ├── tray_icon.py              # System tray icon
        ├── panel_host.py             # QWebEngineView wrapper for React app
        ├── bridge.py                 # Python-side event bus
        ├── bridge_journal.py         # Journal event wiring
        ├── bridge_settings.py        # Settings event wiring
        ├── bridge_pomodoro.py        # Pomodoro event wiring
        └── settings/                 # Legacy settings GUI (fallback)
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

3. Add a GIF in `media/` subfolder (e.g., `sleep.gif`)

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

### Python
- **PyQt6** - GUI framework (pet widget, speech bubble, tray icon)
- **PyQt6-WebEngine** - QWebEngineView for hosting React UI
- **qasync** - Qt-asyncio integration
- **aiohttp** - Async HTTP client (API calls)
- **litellm** - Multi-provider LLM gateway (personality engine, journal cleanup)
- **python-dotenv** - Environment variable management
- **google-api-python-client** - Google Calendar API
- **google-auth-oauthlib** - Google OAuth flow

### React UI (ui/)
- **React 18** + **TypeScript** - Panel UI framework
- **Vite** - Build tool with hot-reload
- **Tailwind CSS 4** - Utility-first styling with design tokens
- **shadcn/ui** - Accessible component primitives
- **Framer Motion** - Page transitions and micro-interactions
- **Recharts** - Charts (weekly pomodoro stats)
- **Lucide React** - Icon set

## License

MIT
