from app.database import SessionLocal
from app.crud import news_exists, create_many_news
from app.models import Post, NewsItem

db = SessionLocal()


print("Перевірка None:", news_exists(db, None))
print("Перевірка наявного URL:", news_exists(db, "https://example.com/news"))
print("Перевірка нового URL:", news_exists(db, "https://example.com/new-news"))
import logging

logging.basicConfig(level=logging.INFO)

post = db.query(Post).filter(Post.news_id == 16).first()
print(post)

news_list = [
    {
        "title": "В Україні запускають нову платформу для IT-навчання",
        "url": "https://example.com/news/it-education-platform-2026",
        "summary": "Нова онлайн-платформа пропонуватиме курси з програмування та веброзробки.",
        "source": "Example",
        "published_at": "2026-11-07",
        "raw_text": "В Україні запускають нову онлайн-платформу для IT-навчання. Користувачі зможуть вивчати Python, JavaScript та основи веброзробки. Платформа орієнтована на початківців."
    },
    {
        "title": "Перевірка масового збереження 2026-11-06",
        "url": "https://example.com/bulk-test-2026-11-06",
        "summary": "Опис другої новини",
        "source": "Example",
        "published_at": "2026-11-03",
        "raw_text": "Повний текст другої новини"
    },
    {
        "title": "Перша нова новина bulk test 2026-11-06",
        "url": "https://example.com/bulk-test-first-2026-11-06",
        "summary": "Опис першої новини",
        "source": "Example",
        "published_at": "2026-11-03",
        "raw_text": "Повний текст першої новини"
    },
    {
        "title": None,
        "url": "https://example.com/error-test-2026",
        "summary": "Тест помилки",
        "source": "Example",
        "published_at": "2026-11-06",
        "raw_text": "Тест перевірки обробки помилок"
    }
]

try:
    test_url = "https://example.com/news"

    exists = news_exists(db, test_url)

    if exists:
        print("Така новина вже є в базі")
    else:
        print("Такої новини ще немає в базі")

    result = create_many_news(db, news_list)
    print("Результат збереження:", result)

    test_url = news_list[0]["url"]
    saved_news = db.query(NewsItem).filter(NewsItem.url == test_url).first()
    if saved_news:
        print(saved_news.title)
    else:
        print("Новину не знайдено")

finally:
    db.close()

