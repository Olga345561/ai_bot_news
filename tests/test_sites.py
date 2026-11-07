from app.news_parser.sites import fetch_and_parse_all_news
from app.database import SessionLocal
from app.news_parser.sites import fetch_and_save_news

db = SessionLocal()

try:
    result = fetch_and_save_news(
        db=db,
        source="Highload",
        base_url="https://highload.tech/"
    )

    print("Результат збереження:", result)

finally:
    db.close()