# Desktop Pet

A modular desktop companion app. Supports pluggable **behaviors** (visual animations) and **integrations** (external service connections). Bring your own sprites!

## Features

- Transparent, draggable desktop pet that stays on top
- **Modular behavior system** - easily add new animations
- **Pluggable integrations** - connect to external services
- **Telegram integration** - alerts when monitored users send messages
- **Weather integration** - pet reacts to local weather (umbrella in rain, sunglasses in sun)
- **Google Calendar integration** - travel-time-aware event alerts with two-phase notifications
- Animated sprites with idle, alert, wander, rainy, sunny, and time-of-day states
- Wandering behavior - pet randomly moves around your screen
- System tray icon with integration controls and API usage display

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

### Telegram

1. Get your API credentials from [my.telegram.org](https://my.telegram.org/apps)
2. Add `API_ID`, `API_HASH`, and `MONITORED_USERS` to `.env`
3. On first run, the terminal will prompt you to:
   - Enter your phone number (with country code, e.g., +1234567890)
   - Enter the verification code sent to your Telegram app
   - Enter your 2FA password (if enabled)
4. The session is saved to `pet_session.session` and reused on subsequent runs

### Weather

1. Get a free API key from [openweathermap.org](https://openweathermap.org/api)
2. Add `OPENWEATHER_API_KEY` to `.env`
3. Set your city in `settings.json` under `integrations.weather.city`

### Google Calendar

1. Create OAuth credentials at [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Enable the **Google Calendar API**
3. Add `GOOGLE_CALENDAR_CLIENT_ID` and `GOOGLE_CALENDAR_CLIENT_SECRET` to `.env`
4. Run the auth script:
   ```bash
   uv run python scripts/auth_google_calendar.py
   ```
5. (Optional) For travel-time alerts, also enable **Routes API** and **Geocoding API**, then add `GOOGLE_MAPS_API_KEY` to `.env`
6. (Optional) For OneMap routing (Singapore), register at [onemap.gov.sg](https://www.onemap.gov.sg/apidocs/register) and add `ONEMAP_EMAIL`/`ONEMAP_PASSWORD` to `.env`

#### OneMap API Notes

OneMap tokens expire every 3 days — the app handles renewal automatically. There is a 300 calls/min rate limit across all OneMap APIs (routing, geocoding, etc.). The app makes at most 2-4 calls per 5-minute cycle, so this limit is unlikely to be reached in normal use.

#### Google Cloud Configuration

**API key restriction**: Restrict your key to only the Geocoding API and Routes API under Credentials > Edit API Key > API restrictions.

**Quota limits**: Set per-minute and per-day limits under Google Maps Platform > Quotas to prevent accidental overage.

Routes API and Geocoding API are **separate SKUs** with independent free pools:

| API | Free Tier | Recommended Quota |
|-----|-----------|-------------------|
| Routes: Compute Routes (Essentials) | 10,000 requests/month | 20/min, 300/day |
| Geocoding | 10,000 requests/month | 10/min, 100/day |

Quota buckets to restrict:
- **Routes API**: `Directions - ComputeRoutes per request quota per minute per user`, `Directions - ComputeRoutes per request quota per minute`, `Directions - ComputeRoutes per request quota per day`
- **Geocoding API**: `v3 requests per minute per user`, `v3 requests per minute`, `v3 requests per day`

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
- **Left-click**: Dismiss alert / provide event location
- **Right-click**: Open context menu (Reset Position, Quit)
- **System tray**: Double-click to show/hide, right-click for menu
- **Tray > Integrations**: Enable/disable integrations
- **Tray > API Usage**: View Google Maps API call counts

### Behavior

The pet will randomly wander around your screen. It reacts to:
- **Telegram messages** from monitored users (bounce + alert sound)
- **Weather conditions** (umbrella sprite in rain, sunglasses in sun)
- **Calendar events** with two-phase travel alerts:
  - *Prepare alert* (speech bubble) when it's time to get ready
  - *Leave alert* (bounce + sound) when it's time to depart
  - Falls back to a flat 30-minute alert if no routing API is configured
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
    "telegram": {
      "enabled": true,
      "trigger_behavior": "alert"
    },
    "weather": {
      "enabled": true,
      "city": "New York",
      "units": "imperial",
      "check_interval_ms": 1800000
    },
    "google_calendar": {
      "enabled": false,
      "check_interval_ms": 300000,
      "alert_before_minutes": 30,
      "trigger_behavior": "alert",
      "calendar_id": "primary",
      "origin_address": "",
      "preparation_minutes": 15,
      "travel_modes": ["DRIVE", "TRANSIT"],
      "fetch_window_minutes": 120,
      "api_quota_limit": 9500
    }
  }
}
```

### Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | For Telegram | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | For Telegram | Telegram API Hash |
| `MONITORED_USERS` | For Telegram | Comma-separated Telegram user IDs to monitor |
| `OPENWEATHER_API_KEY` | For Weather | API key from [openweathermap.org](https://openweathermap.org/api) |
| `GOOGLE_CALENDAR_CLIENT_ID` | For Calendar | OAuth client ID from Google Cloud Console |
| `GOOGLE_CALENDAR_CLIENT_SECRET` | For Calendar | OAuth client secret |
| `GOOGLE_MAPS_API_KEY` | Optional | For travel-time alerts (Routes + Geocoding APIs) |
| `ONEMAP_EMAIL` | Optional | [OneMap Singapore](https://www.onemap.gov.sg/apidocs/register) fallback routing |
| `ONEMAP_PASSWORD` | Optional | OneMap password |

### Travel-Time Alert Providers

The calendar integration uses a cascading provider system for travel-time calculations:

1. **Google Routes API** - used if `GOOGLE_MAPS_API_KEY` is set and quota available
2. **OneMap Singapore** - used if `ONEMAP_EMAIL`/`ONEMAP_PASSWORD` are set (with Nominatim geocoding)
3. **Flat alert** - 30-minute fixed alert if no routing credentials are configured

Set `origin_address` in `settings.json` under `google_calendar` to enable travel-time alerts.

The app's internal tracker (configurable via `api_quota_limit`, default 9,500) provides an additional safety net per API.

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
│   ├── telegram/
│   ├── weather/
│   └── google_calendar/
│       ├── integration.py            # Two-phase alert logic
│       ├── calendar_event.py         # Event model
│       ├── routes.py                 # Google Routes API client
│       ├── geocoding.py              # Geocoding (Google + Nominatim)
│       ├── onemap.py                 # OneMap Singapore routing
│       └── usage_tracker.py          # API quota tracking
│
└── src/
    ├── core/
    │   ├── base_integration.py       # Abstract integration class
    │   ├── behavior_registry.py      # Behavior discovery & management
    │   └── integration_manager.py    # Integration lifecycle
    └── ui/
        ├── pet_window.py             # Desktop pet widget
        ├── speech_bubble.py          # Speech bubble overlay
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
- **Telethon** - Telegram client library
- **aiohttp** - Async HTTP client (API calls)
- **python-dotenv** - Environment variable management
- **google-api-python-client** - Google Calendar API
- **google-auth-oauthlib** - Google OAuth flow

## License

MIT
