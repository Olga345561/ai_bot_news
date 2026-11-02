from datetime import timezone, datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.encoders import isoformat
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.schemas import NewsItemCreate
from app.database import Base, engine, SessionLocal
from app.models import NewsItem as NewsItemModel, Post
from app.ai.generator import generate_post
from app.utils import matches_keywords
from app.crud import news_exists
from app import models

app = FastAPI(title="AI_bot_news")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Наш проєкт працює!"}

@app.post("/news")
def create_news(news: NewsItemCreate, db: Session = Depends(get_db)):
    # Перевіряємо, чи новина вже є в базі
    if news.url and news_exists(db, news.url):
        raise HTTPException(
            status_code=409,
            detail="Така новина вже є в базі"
        )
    # Зберігаємо новину
    db_news = NewsItemModel(
        title=news.title,
        url=news.url,
        summary=news.summary,
        source=news.source,
        published_at=news.published_at,
        raw_text=news.raw_text
    )

    db.add(db_news)
    try:
        db.commit()
        db.refresh(db_news)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Така новина вже є в базі")

    # Перевіряємо наявність ключових слів
    keywords = ['Python', 'AI', 'технології']

    if not matches_keywords(
        db_news.title,
        db_news.raw_text,
        keywords,
    ):
        return {
            "messages":"Новина не відповідає ключовим словам",
            "news_id": db_news.id,
            "status": "filtered",
        }

    # Генеруємо допис за допомогою ШІ
    try:
        generated_text = generate_post(
            db_news.title,
            db_news.raw_text,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Не вдалося згенерувати допис: {e}")

    # Зберігаємо згенерований допис
    db_post = Post(
        news_id=db_news.id,
        generated_text=generated_text,
        published_at=datetime.now(timezone.utc).isoformat(),
        status="generated",
    )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    # Повертаємо результат
    return {
        "message": "Новину збережено, допис згенеровано",
        "news_id": db_news.id,
        "post_id": db_post.id,
        "title": db_news.title,
        "generated_text": db_post.generated_text,
        "status": db_post.status,
    }

