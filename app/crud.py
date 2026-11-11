
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models import NewsItem
from app.ai.translator import translate_news


logger = logging.getLogger(__name__)


def news_exists(db: Session, url: str) -> bool:
    if not url:
        return False

    news = db.query(NewsItem).filter(NewsItem.url == url).first()
    return news is not None


def news_exists_by_title(db: Session, title: str) -> bool:
    if not title:
        return False

    news = db.query(NewsItem).filter(NewsItem.title == title).first()
    return news is not None


# Створює одну новину та додає її до сесії бази даних
def create_news(db: Session, news_data: dict):
    db_news = NewsItem(
        title=news_data["title"],
        url=news_data["url"],
        summary=news_data["summary"],
        source=news_data["source"],
        published_at=news_data["published_at"],
        raw_text=news_data["raw_text"],
    )

    db.add(db_news)
    return db_news


# Перевіряє новини, перекладає їх та зберігає в базу
def create_many_news(db: Session, news_list: list) -> dict:
    added_count = 0
    skipped_count = 0

    try:
        for news_data in news_list:

            # Перевіряємо наявність обов'язкових даних
            if not news_data.get("title") or not news_data.get("raw_text"):
                skipped_count += 1
                continue

            # Перевіряємо дублікати до перекладу
            if (
                news_exists(db, news_data.get("url"))
                or news_exists_by_title(db, news_data["title"])
            ):
                skipped_count += 1
                continue

            # Перекладаємо новину українською
            translated = translate_news(
                title=news_data["title"],
                summary=news_data.get("summary") or "",
                raw_text=news_data["raw_text"]
            )

            # Замінюємо оригінальні тексти перекладеними
            news_data = {
                **news_data,
                **translated
            }

            # Додаємо перекладену новину до бази
            create_news(db, news_data)
            added_count += 1

        db.commit()

        logger.info(
            "Збереження новин завершено. Додано: %s, пропущено: %s",
            added_count,
            skipped_count
        )

    except Exception:
        db.rollback()
        logger.exception("Не вдалося перекласти або зберегти список новин")
        skipped_count += added_count
        added_count = 0

    return {
        "saved": added_count,
        "skipped": skipped_count,
    }
