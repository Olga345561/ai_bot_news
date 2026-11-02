from app.database import SessionLocal
from app.crud import news_exists
from app.models import Post

db = SessionLocal()

post = db.query(Post).filter(Post.news_id == 16).first()
print(post)

try:
    test_url = "https://example.com/news"

    result = news_exists(db, test_url)

    if result:
        print("Така новина вже є в базі")
    else:
        print("Такої новини ще немає в базі")

finally:
    db.close()