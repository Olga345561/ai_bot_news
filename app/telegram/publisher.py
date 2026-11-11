
import logging

from app.telegram.bot import get_telegram_client

logger = logging.getLogger(__name__)


async def publish_post(text: str):
    client = get_telegram_client()

    try:
        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError("Потрібна авторизація Telegram!")

        message = await client.send_message(
            "@ai_news_today_ua",
            text
        )

        logger.info(
            "Пост успішно опубліковано: message_id=%s",
            message.id
        )

        return {
            "ok": True,
            "message_id": message.id
        }

    except Exception:
        logger.exception("Помилка під час публікації в Telegram")
        raise

    finally:
        if client.is_connected():
            await client.disconnect()