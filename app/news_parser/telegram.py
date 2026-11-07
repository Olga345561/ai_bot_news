import os
from dotenv import load_dotenv
from telethon import TelegramClient
from app.database import SessionLocal
from app.crud import create_many_news
import asyncio

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient("telegram_qr_session", API_ID, API_HASH)

async def main():
    await client.connect()

    try:
        if await client.is_user_authorized():
            print("Авторизація успішна!")

            news_list = await parse_telegram_messages(
                client, "ua_1techno", 30
            )

            print(f"Отримано новин: {len(news_list)}")

            db = SessionLocal()

            try:
                result = create_many_news(db, news_list)
                print("Результат збереження:", result)
            finally:
                db.close()

        else:
            print("Потрібна авторизація!")

    finally:
        await client.disconnect()

async def parse_telegram_messages(client, channel, limit=30):
    news_list = []
    async for message in client.iter_messages(channel, limit=limit):
        if not message.message:
            continue

        raw_text = message.message.strip()

        lines = raw_text.splitlines()

        title = lines[0].strip()
        summary = "\n".join(lines[1:]).strip()

        news_data = {
            "title": title,
            "url": f"https://t.me/ua_1techno/{message.id}",
            "summary": summary or title,
            "source": "Перший Технологічний • Нейромережі • Стартапи",
            "published_at": message.date.isoformat(),
            "raw_text": raw_text
        }

        news_list.append(news_data)
    return news_list

if __name__ == "__main__":
    asyncio.run(main())
