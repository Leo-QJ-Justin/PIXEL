# Haro Desktop Pet

A desktop companion app featuring Haro from Gundam SEED that alerts you when specific contacts message you on Telegram.

## Features

- Transparent, draggable desktop pet that stays on top
- Telegram integration to monitor messages from VIP contacts
- Visual and audio alerts when monitored users send messages
- Animated sprites with idle, alert, and flying states
- Wandering behavior - Haro randomly flies around your screen
- System tray icon for easy access
- Configurable watchlist of monitored users

## Requirements

- Python 3.10+
- uv (Python package manager)
- Telegram API credentials

## Installation

1. Clone the repository and navigate to the project folder

2. Install dependencies with UV:
   ```bash
   uv sync
   ```

3. Get your Telegram API credentials from [my.telegram.org](https://my.telegram.org)

4. Configure your `.env` file:
   ```
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here
   ```

5. Add your sprite images to `assets/sprites/`:
   - `idle_1.png`, `idle_2.png` - Idle animation frames
   - `alert_1.png`, `alert_2.png` - Alert animation frames
   - `fly_1.png`, `fly_2.png`, `fly_3.png`, `fly_4.png` - Flying/wandering animation frames

6. (Optional) Add alert sound to `assets/sounds/`:
   - `haro_alert.wav`

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

To run Haro in the background so it persists after closing the terminal:
```powershell
Start-Process '.venv\Scripts\pythonw.exe' -ArgumentList 'main.py' -WindowStyle Hidden
```

Or if using `pythonw` globally:
```powershell
Start-Process pythonw -ArgumentList 'main.py' -WindowStyle Hidden
```

On first run, you'll be prompted to authenticate with Telegram.

### Controls

- **Left-click + drag**: Move Haro around the screen
- **Left-click**: Dismiss alert
- **Right-click**: Open context menu (Reset Position, Quit)
- **System tray**: Double-click to show/hide, right-click for menu

### Behavior

Haro will randomly wander around your screen, flying left or right every few seconds. When a monitored user sends a message, Haro will bounce and play an alert sound until you click to dismiss.

### Managing Monitored Users

Edit `settings.json` to add Telegram user IDs to monitor:
```json
{
  "monitored_users": [123456789, 987654321]
}
```

To find a user's ID, you can check the debug logs when they send you a message - the ID will be printed in the console.

### Debugging

The application outputs debug logs to the console showing:
- Incoming Telegram messages and sender IDs
- Monitored user detection
- Alert triggers

Run with `uv run python main.py` to see logs in the terminal.

## Dependencies

- **PyQt6** - GUI framework
- **Telethon** - Telegram client library
- **qasync** - Qt-asyncio integration
- **python-dotenv** - Environment variable management

## Project Structure

```
├── main.py                 # Application entry point
├── config.py               # Configuration and settings management
├── settings.json           # Monitored users list (created on first run)
├── assets/
│   ├── sprites/            # PNG images for pet states
│   │   ├── idle_1.png, idle_2.png      # Idle animation
│   │   ├── alert_1.png, alert_2.png    # Alert animation
│   │   └── fly_1-4.png                 # Flying animation
│   └── sounds/             # Alert sounds
└── src/
    ├── ui/
    │   ├── haro_window.py  # Desktop pet widget
    │   └── tray_icon.py    # System tray icon
    └── services/
        └── telegram_service.py  # Telegram message listener
```

## License

MIT
