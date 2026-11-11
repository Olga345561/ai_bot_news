
import logging

from app.ai.openai_client import client

logger = logging.getLogger(__name__)


def translate_news(title: str, summary: str, raw_text: str) -> dict:
    """Перекладає заголовок, опис і повний текст новини українською."""

    logger.info("Початок перекладу новини: %s", title)

    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ти професійний перекладач новин українською мовою. "
                        "Переклади надану новину українською. "
                        "Якщо текст уже українською, збережи його без змін. "
                        "Не вигадуй і не змінюй факти, дати, цифри, "
                        "імена, назви компаній та організацій. "
                        "Поверни результат строго у форматі JSON "
                        "з трьома полями: title, summary, raw_text. "
                        "Не додавай пояснень поза JSON."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Заголовок:\n{title}\n\n"
                        f"Короткий опис:\n{summary}\n\n"
                        f"Повний текст:\n{raw_text}"
                    )
                }
            ],
            response_format={"type": "json_object"}
        )

        import json

        content = response.choices[0].message.content

        if not content:
            raise ValueError("ШІ не повернув результат перекладу")

        translated = json.loads(content)

        result = {
            "title": translated["title"].strip(),
            "summary": translated["summary"].strip(),
            "raw_text": translated["raw_text"].strip(),
        }

        if not all(result.values()):
            raise ValueError("Перекладач повернув порожнє поле")

        logger.info("Переклад успішно завершено: %s", title)

        return result

    except Exception:
        logger.exception("Помилка перекладу новини: %s", title)
        raise
