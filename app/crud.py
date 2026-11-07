from sqlalchemy.orm import Session
from app.models import NewsItem
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def news_exists(db: Session, url:str) -> bool:
    if not url:
        return False
    news= db.query(NewsItem).filter(NewsItem.url == url).first()
    return news is not None

def news_exists_by_title(db: Session, title:str) -> bool:
    if not title:
        return False
    news = db.query(NewsItem).filter(NewsItem.title == title).first()
    return news is not None

#створює одну новину та зберігає її в базу
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

#проходить циклом по списку новин і викликає create_news() для кожної
def create_many_news(db: Session, news_list: list) -> dict:
    added_count = 0
    skipped_count = 0

    try:
        for news_data in news_list:
            if not news_data["title"] or not news_data["raw_text"]:
                skipped_count += 1
                continue

            if news_exists(db, news_data["url"]) or news_exists_by_title(db, news_data["title"]):
                skipped_count += 1
                continue

            create_news(db, news_data)
            added_count += 1

        db.commit()

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Не вдалося зберегти список новин")
        skipped_count += added_count
        added_count = 0

    return {
        "saved": added_count,
        "skipped": skipped_count,
    }
