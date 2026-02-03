import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

async def authenticate():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    client = TelegramClient('haro_session', api_id, api_hash)
    await client.start()
    print("Success! Session created.")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(authenticate())
