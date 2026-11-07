from celery_worker import celery_app
from app.database import SessionLocal
from app.news_parser.sites import fetch_and_save_news


@celery_app.task
def test_task():
    return "Celery працює!"

@celery_app.task
def parse_site_news(source: str, base_url: str):
    db = SessionLocal()

    try:
        result = fetch_and_save_news(
            db,
            source=source,
            base_url=base_url
        )
        return result

    finally:
        db.close()