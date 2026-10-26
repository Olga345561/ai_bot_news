from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from app.database import Base

class NewsItem(Base):
    __tablename__ = 'news_item'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    summary = Column(String, nullable=False)
    source = Column(String, nullable=False)
    published_at = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)

class Post(Base):
    __tablename__ = 'post'
    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey('news_item.id'))
    generated_text = Column(String, nullable=False)
    published_at = Column(String, nullable=False)
    status = Column(String, nullable=False)

class Source(Base):
    __tablename__ = 'source'
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    name = Column(String, nullable=True)
    url = Column(String, nullable=True)
    enabled = Column(Boolean, nullable=True)

class Keyword(Base):
    __tablename__ = 'keyword'
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False)


