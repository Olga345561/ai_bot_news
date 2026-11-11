
import os

from app.logging_config import configure_logging
from celery import Celery

configure_logging()

redis_broker = os.getenv(
    "REDIS_BROKER_URL",
    "redis://localhost:6379/0"
)

redis_backend = os.getenv(
    "REDIS_BACKEND_URL",
    "redis://localhost:6379/1"
)

celery_app = Celery(
    "ai_bot_news",
    broker=redis_broker,
    backend=redis_backend,
    include=["app.tasks"]
)

celery_app.conf.beat_schedule = {
    "run-news-pipeline-every-30-minutes": {
        "task": "app.tasks.run_news_pipeline",
        "schedule": 1800.0,
    },
}

celery_app.conf.timezone = "Europe/Kyiv"
