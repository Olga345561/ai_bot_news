
import logging
import asyncio

from app.database import SessionLocal
from app.crud import create_many_news
from app.telegram.bot import get_telegram_client
from telethon import TelegramClient


logger = logging.getLogger(__name__)


# Підключається до Telegram, викликає парсер і зберігає новини
async def main(channel: str, source: str, limit: int = 30):
    client = get_telegram_client()

    logger.info(
        "Початок парсингу Telegram: channel=%s, source=%s, limit=%s",
        channel,
        source,
        limit
    )

    try:
        await client.connect()
        logger.info("Підключення до Telegram успішне")

        if not await client.is_user_authorized():
            raise RuntimeError("Потрібна авторизація Telegram!")

        logger.info("Авторизація Telegram успішна")

        news_list = await parse_telegram_messages(
            client, channel, source, limit
        )

        logger.info("Отримано повідомлень із новинами: %s", len(news_list))

        db = SessionLocal()

        try:
            result = create_many_news(db, news_list)

            logger.info(
                "Збереження Telegram-новин завершено: saved=%s, skipped=%s",
                result.get("saved", 0),
                result.get("skipped", 0)
            )

            return result

        except Exception:
            logger.exception("Помилка під час збереження Telegram-новин")
            raise

        finally:
            db.close()
            logger.info("З'єднання з базою даних закрито")

    except Exception:
        logger.exception(
            "Помилка під час парсингу Telegram-каналу: %s",
            channel
        )
        raise

    finally:
        if client.is_connected():
            await client.disconnect()
            logger.info("З'єднання з Telegram закрито")


# Отримує повідомлення з Telegram і перетворює їх на список словників
async def parse_telegram_messages(
    client: TelegramClient,
    channel: str,
    source: str,
    limit: int = 30
):
    news_list = []

    logger.info("Початок отримання повідомлень із каналу: %s", channel)

    try:
        async for message in client.iter_messages(channel, limit=limit):

            if not message.message:
                logger.debug(
                    "Повідомлення без тексту пропущено: message_id=%s",
                    message.id
                )
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

        logger.info(
            "Отримання повідомлень завершено: channel=%s, count=%s",
            channel,
            len(news_list)
        )

        return news_list

    except Exception:
        logger.exception(
            "Помилка під час отримання повідомлень із каналу: %s",
            channel
        )
        raise


if __name__ == "__main__":
    asyncio.run(main())
