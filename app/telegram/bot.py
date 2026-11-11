import os
from dotenv import load_dotenv
from telethon import TelegramClient
from pathlib import Path

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

SESSION_NAME = "telegram_qr_session"

BASE_DIR = Path(__file__).resolve().parents[2]
SESSION_PATH = str(BASE_DIR / SESSION_NAME)


def get_telegram_client():
    return TelegramClient(
        SESSION_PATH,
        API_ID,
        API_HASH
    )