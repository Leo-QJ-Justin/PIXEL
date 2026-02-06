"""Test script to run telegram service standalone for debugging."""

import asyncio

from telethon import TelegramClient, events

from config import API_HASH, API_ID, get_monitored_users


async def main():
    print("=" * 50)
    print("TELEGRAM SERVICE DEBUG TEST")
    print("=" * 50)
    print(f"API_ID configured: {bool(API_ID)}")
    print(f"API_HASH configured: {bool(API_HASH)}")

    if not API_ID or not API_HASH:
        print("Error: API_ID and API_HASH not configured in .env file")
        return

    monitored = get_monitored_users()
    print(f"\nMonitored user IDs: {monitored}")
    if not monitored:
        print("WARNING: No monitored users! Add users via tray menu.")
    print("=" * 50)

    client = TelegramClient("pet_session", API_ID, API_HASH)

    @client.on(events.NewMessage(incoming=True))
    async def handle_new_message(event):
        sender = await event.get_sender()
        sender_id = event.sender_id
        sender_name = getattr(sender, "first_name", "Unknown")
        is_monitored = sender_id in get_monitored_users()

        print(f"\n{'=' * 50}")
        print("NEW MESSAGE RECEIVED")
        print(f"{'=' * 50}")
        print(f"From: {sender_name}")
        print(f"Sender ID: {sender_id}")
        print(f"Message: {event.message.text[:100] if event.message.text else '[no text]'}")
        print(f"{'=' * 50}")

        if is_monitored:
            print(">>> WOULD TRIGGER ALERT! <<<")
            print(f">>> Pet should react to: {sender_name}")
        else:
            print("NOT in monitored list - no alert")
            print(f"To add this user, copy ID: {sender_id}")
        print(f"{'=' * 50}\n")

    await client.start()
    print("\nTelegram client connected!")
    print("Listening for messages... (Ctrl+C to stop)\n")

    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
