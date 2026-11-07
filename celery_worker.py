from celery import Celery

celery_app = Celery(
    "ai_bot_news",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["app.tasks"]
)