import os
from dotenv import load_dotenv
from telethon import TelegramClient
from app.database import SessionLocal
from app.crud import create_many_news
import asyncio

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")


#Підключається до Telegram, викликає парсер і зберігає новини
async def main(channel:str, source:str, limit:int=30):
    client = TelegramClient("telegram_qr_session", API_ID, API_HASH)

    await client.connect()

    try:
        if await client.is_user_authorized():
            print("Авторизація успішна!")

            news_list = await parse_telegram_messages(
                client, channel, source, limit
            )

            print(f"Отримано новин: {len(news_list)}")

            db = SessionLocal()

            try:
                result = create_many_news(db, news_list)
                print("Результат збереження:", result)
                return result
            finally:
                db.close()

        else:
            raise RuntimeError("Потрібна авторизація Telegram!")

    finally:
        await client.disconnect()
#Отримуємо повідомлення з Telegram і перетворюємо їх на список словників
async def parse_telegram_messages(
    client: TelegramClient,
    channel: str,
    source: str,
    limit: int = 30):

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
            "url": f"https://t.me/{channel}/{message.id}",
            "summary": summary or title,
            "source": source,
            "published_at": message.date.isoformat(),
            "raw_text": raw_text
        }

        news_list.append(news_data)
    return news_list

if __name__ == "__main__":
    asyncio.run(main())
