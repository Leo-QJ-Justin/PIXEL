# Telegram Integration

Monitors Telegram for messages from VIP contacts and triggers alerts.

## Setup

1. Get API credentials from https://my.telegram.org/apps
2. Add to your `.env` file:
   ```
   API_ID=your_api_id
   API_HASH=your_api_hash
   MONITORED_USERS=123456789,987654321
   ```
3. Run the app and authenticate with your phone number + verification code
4. Session is cached in `pet_session.session`

## Finding User IDs

To find a Telegram user's ID:
1. Forward a message from them to [@userinfobot](https://t.me/userinfobot)
2. The bot will reply with their user ID

## Configuration

In `settings.json`:
```json
{
  "integrations": {
    "telegram": {
      "enabled": true,
      "trigger_behavior": "alert"
    }
  }
}
```

| Setting | Type | Description |
|---------|------|-------------|
| `enabled` | bool | Enable/disable the integration |
| `trigger_behavior` | string | Behavior to trigger on message (default: "alert") |

Monitored users are configured in `.env` for security (not committed to repo).
