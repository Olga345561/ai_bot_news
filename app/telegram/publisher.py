import os
from dotenv import load_dotenv
import requests

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def publish_post(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": "@ai_news_today_ua",
        "text": text
    }

    response = requests.post(url, json=payload, timeout=(5, 30))

    response.raise_for_status()

    return response.json()