import logging
from app.ai.openai_client import client

logger = logging.getLogger(__name__)


def generate_post(title: str, text: str) -> str:
    logger.info("Початок генерації допису: %s", title)

    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ти професійний редактор українського Telegram-каналу "
                        "про штучний інтелект і технології. "

                        "Створи короткий, зрозумілий та інформативний допис "
                        "на основі наданої новини. "

                        "Суворо дотримуйся правил: "
                        "1. Використовуй тільки факти з тексту новини. "
                        "2. Не вигадуй дати, цифри, назви, цитати та характеристики. "
                        "3. Не додавай інформацію, якої немає у джерелі. "
                        "4. Не повторюй одну думку кілька разів. "
                        "5. Якщо певна інформація незрозуміла, краще пропусти її. "
                        "6. Не змінюй зміст оригінальної новини. "

                        "Структура допису: "
                        "короткий заголовок з доречним емодзі, "
                        "основна інформація та важливі подробиці. "

                        "Пиши природною українською мовою. "
                        "Не додавай власних висновків і непідтверджених прогнозів."
                    )
                },
                {
                    "role": "user",
                    "content": f"Заголовок: {title}\n\nТекст новини:\n{text}"
                }
            ]
        )

        generated_text = response.choices[0].message.content

        if not generated_text:
            logger.warning("ШІ повернув порожній текст: %s", title)
            raise ValueError("ШІ не повернув текст допису")

        logger.info("Допис успішно згенеровано: %s", title)

        return generated_text.strip()

    except Exception:
        logger.exception("Помилка генерації допису: %s", title)
        raise
