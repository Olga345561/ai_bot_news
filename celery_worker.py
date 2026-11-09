from celery import Celery

celery_app = Celery(
    "ai_bot_news",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["app.tasks"]
)

celery_app.conf.beat_schedule = {
    "parse-highload-every-30-minutes": {
        "task": "app.tasks.parse_site_news",
        "schedule": 1800.0,
        "args": ("Highload", "https://highload.tech/"),
    },
    "parse-telegram-every-30-minutes": {
        "task": "app.tasks.parse_telegram_news",
        "schedule": 1800.0,
        "args": (
            "ua_1techno",
            "Перший Технологічний • Нейромережі • Стартапи",
            30
        ),
    },
}

celery_app.conf.timezone = "Europe/Kyiv"