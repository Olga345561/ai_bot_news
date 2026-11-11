from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import NewsItem, Post, Source, Keyword
from app.api.schemas import SourceCreate, KeywordCreate, KeywordUpdate, SourceUpdate
from app.tasks import generate_posts_for_news

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/news/")
def get_news(db: Session = Depends(get_db)):
    news = db.query(NewsItem).order_by(NewsItem.id.desc()).all()

    return news

@router.get("/posts/")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.id.desc()).all()
    return posts



@router.post("/sources/")
def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    existing_source = db.query(Source).filter(
        Source.type == source.type,
        Source.url == source.url
    ).first()

    if existing_source:
        raise HTTPException(
            status_code=409,
            detail="Таке джерело вже існує"
        )
    db_source = Source(
        type=source.type,
        name=source.name,
        url=source.url,
        enabled=source.enabled
    )

    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    return db_source

@router.get("/sources/")
def get_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.id.desc()).all()
    return sources

@router.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Джерело не знайдено"
        )

    db.delete(source)
    db.commit()

    return {"message": "Джерело успішно видалено"}

@router.patch("/sources/{source_id}/enabled")
def update_source_enabled(
    source_id: int,
    source_data: SourceUpdate,
    db: Session = Depends(get_db)
):
    source = db.query(Source).filter(
        Source.id == source_id
    ).first()

    if not source:
        raise HTTPException(
            status_code=404,
            detail="Джерело не знайдено"
        )

    source.enabled = source_data.enabled
    db.commit()
    db.refresh(source)

    return {
        "message": "Статус джерела успішно оновлено",
        "id": source.id,
        "enabled": source.enabled
    }

@router.get("/keywords/")
def get_keywords(db: Session = Depends(get_db)):
    return db.query(Keyword).order_by(Keyword.id.desc()).all()

@router.post("/keywords/")
def create_keyword(keyword: KeywordCreate, db: Session = Depends(get_db)):
    db_keyword = Keyword(word=keyword.word)

    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)

    return db_keyword

@router.put("/keywords/{keyword_id}")
def update_keyword(
    keyword_id: int,
    keyword_data: KeywordUpdate,
    db: Session = Depends(get_db)
):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()

    if keyword is None:
        raise HTTPException(
            status_code=404,
            detail="Ключове слово не знайдено"
        )

    keyword.word = keyword_data.word

    db.commit()
    db.refresh(keyword)

    return keyword

@router.delete("/keywords/{keyword_id}")
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()

    if keyword is None:
        raise HTTPException(status_code=404, detail="Ключове слово не знайдено")

    db.delete(keyword)
    db.commit()

    return {"message": "Ключове слово успішно видалено"}

@router.post("/generate/")
def generate_posts():
    task = generate_posts_for_news.delay()

    return {
        "message": "Генерацію дописів запущено",
        "task_id": task.id
    }
