# PIXEL

**P**ersonal **I**nteractive e**X**tensible **E**veryday **L**ife companion — a modular desktop pet with a built-in productivity dashboard. Bring your own sprites!

## Features

### Desktop Pet
- Transparent, draggable desktop companion that stays on top
- Animated GIF sprites with idle, wander, sleep, and time-of-day states
- Right-click the pet to open the dashboard
- Speech bubbles with optional AI personality (OpenAI, OpenRouter, Ollama via litellm)

### Dashboard
A full productivity hub accessible from the pet, system tray, or tray double-click.

- **Home** — at-a-glance summary of all integrations: tasks due, habits done, focus time, screen time, journal status, and next calendar event
- **Tasks** — local todo list with deadlines, tags, subtasks, and priority. Pet nudges about overdue items and celebrates completions.
- **Journal** — daily journaling with mood tracking, calendar heat map, blurred vault, and optional LLM text cleanup
- **Focus (Pomodoro)** — timer with progress ring, session tracking, diamond streak, and weekly stats
- **Habits** — flexible habit tracker (daily, weekly, X-times-per-week) with streak tracking, reminder nudges, and milestone celebrations
- **Screen Time** — cross-platform app usage tracking with daily timeline, category breakdown (Productive/Neutral/Distracting), weekly charts, and break reminders
- **Workspaces** — group apps, URLs, and folders into named contexts. One-click launch with optional pet behavior per workspace.
- **Settings** — configure behaviors, integrations, AI personality, and more

### Integrations
- **Weather** — pet reacts to local weather conditions
- **Google Calendar** — day preview on startup, countdown reminders at 30/5/0 minutes
- **AI Personality** — optional LLM-powered speech enrichment via litellm

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+ and npm (for building the React UI)

## Installation

### Quick Setup

```bash
./setup.sh
```

### Manual Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Leo-QJ-Justin/PIXEL.git
   cd PIXEL
   ```

2. Install Python dependencies:
   ```bash
   uv sync
   ```

3. Build the React UI:
   ```bash
   cd ui && npm install && npm run build && cd ..
   ```

4. Add your sprites — place GIF files in each `behaviors/*/media/` directory:
   ```
   behaviors/idle/media/idle.gif        # Required — default resting state
   behaviors/wander/media/wander.gif    # Pet moves around screen
   behaviors/sleep/media/sleep.gif      # Inactivity sleep state
   behaviors/wave/media/wave.gif        # Greeting/celebration reaction
   behaviors/yawn/media/yawn.gif        # Idle variety
   ...
   ```
   Each behavior folder has a `config.json` describing timing and priority. You just need to supply the GIF.

5. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (optional)
   ```

## Usage

```bash
uv run python main.py
```

### Controls

- **Left-click + drag** — move the pet
- **Left-click** — tap reaction
- **Right-click pet** — open dashboard
- **System tray** — double-click to open dashboard, right-click for quick actions

### Running in Background (Windows)

```powershell
Start-Process '.venv\Scripts\pythonw.exe' -ArgumentList 'main.py' -WindowStyle Hidden
```

### React UI Development Mode

```bash
# Terminal 1: Vite dev server with hot-reload
cd ui && npm run dev

# Terminal 2: App loads UI from Vite instead of built files
PIXEL_DEV_UI=1 uv run python main.py
```

## Adding Sprites

Each behavior is a folder in `behaviors/` with:

```
behaviors/my_behavior/
├── config.json          # Timing, priority, loop settings
└── media/
    └── my_behavior.gif  # Your animated sprite
```

Example `config.json`:
```json
{
  "frame_duration_ms": 500,
  "loop": true,
  "priority": 2,
  "can_be_interrupted": true
}
```

Sprites are gitignored — each user provides their own character. The app discovers and loads whatever GIFs are present.

### Creating Your Own Sprites

Two free approaches:

1. **Gemini + sprite sheet** — Use Google's Gemini (nano/flash) to generate a sprite sheet of your character in different poses. Split the sheet into individual frames, then combine into a GIF using any GIF maker.

2. **Ludo.ai** — Use the free tier at [ludo.ai](https://ludo.ai) to generate animated sprites from a single base image. Export as GIF and drop into the behavior's `media/` folder.

Each behavior needs one GIF. Recommended size: 80-120px, transparent background.

## Configuration

### Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENWEATHER_API_KEY` | For Weather | API key from [openweathermap.org](https://openweathermap.org/api) |
| `GOOGLE_CALENDAR_CLIENT_ID` | For Calendar | OAuth client ID from Google Cloud Console |
| `GOOGLE_CALENDAR_CLIENT_SECRET` | For Calendar | OAuth client secret |
| `LLM_API_KEY` | No | API key for AI personality engine |
| `LLM_ENDPOINT` | No | Custom endpoint (e.g. for Ollama) |

### settings.json

Runtime configuration is managed through the Settings page in the dashboard. The file is created automatically on first run.

## Tech Stack

### Platform-Specific Setup

**Screen time tracking** works cross-platform but needs extra setup on macOS and Linux:

- **macOS**: `uv sync --extra macos` (installs pyobjc for window tracking)
- **Linux**: `sudo apt install xdotool xprintidle` (X11 only — Wayland not supported)
- **Windows**: works out of the box (uses ctypes + psutil)

### Python Backend
- **PyQt6** — desktop pet widget, system tray, window management
- **PyQt6-WebEngine** — QWebEngineView hosting the React dashboard
- **qasync** — Qt + asyncio integration
- **litellm** — multi-provider LLM gateway
- **psutil** — process info for screen time tracking

### React Dashboard (ui/)
- **React 19** + **TypeScript** — dashboard UI
- **Vite** — build tool
- **Tailwind CSS 4** — utility-first styling with warm design tokens
- **shadcn/ui** — accessible component primitives
- **Framer Motion** — animations and page transitions
- **Recharts** — charts (weekly stats, screen time)
- **Lucide React** — icon set

## Project Structure

```
├── main.py                          # Entry point
├── config.py                        # Configuration loader
├── behaviors/                       # Sprite behaviors (user-provided GIFs)
│   ├── idle/                        # Default resting state
│   ├── wander/                      # Random movement
│   ├── sleep/                       # Inactivity sleep
│   └── ...                          # wave, yawn, rainy, etc.
├── integrations/                    # Pluggable service integrations
│   ├── tasks/                       # Todo list (SQLite)
│   ├── habits/                      # Habit tracking (SQLite)
│   ├── screen_time/                 # App usage tracking (SQLite)
│   ├── workspaces/                  # App launcher (JSON)
│   ├── journal/                     # Daily journaling (SQLite)
│   ├── pomodoro/                    # Focus timer
│   ├── weather/                     # Weather reactions
│   └── google_calendar/             # Calendar reminders
├── src/
│   ├── core/                        # Behavior registry, integration manager
│   ├── ui/                          # Pet widget, panel host, bridge, tray
│   └── services/                    # AI personality engine
├── ui/                              # React dashboard (Vite + TypeScript)
│   ├── src/
│   │   ├── pages/                   # Home, Tasks, Journal, Focus, Habits, Screen Time, Workspaces, Settings
│   │   ├── components/              # PanelLayout, Sidebar, TitleBar, shadcn/ui
│   │   └── bridge/                  # Typed event bus (QWebChannel)
│   └── dist/                        # Built production bundle
└── scripts/                         # Setup and auth utilities
```

## License

MIT
