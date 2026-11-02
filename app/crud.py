from sqlalchemy.orm import Session
from app.models import NewsItem

def news_exists(db: Session, url:str) -> bool:
    news= db.query(NewsItem).filter(NewsItem.url == url).first()
    return news is not None