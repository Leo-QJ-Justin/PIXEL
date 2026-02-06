import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

# Change to project root so session file is created there
os.chdir(Path(__file__).parent.parent)

load_dotenv()


async def authenticate():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    client = TelegramClient("pet_session", api_id, api_hash)
    await client.start()
    print("Success! Session created.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(authenticate())
