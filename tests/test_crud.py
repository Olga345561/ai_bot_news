
import pytest

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import NewsItem
from app.crud import (
    news_exists,
    news_exists_by_title,
    create_news,
    create_many_news,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def news_data():
    return {
        "title": "Тестова новина",
        "url": "https://example.com/news-1",
        "summary": "Короткий опис",
        "source": "Test source",
        "published_at": "2026-11-11",
        "raw_text": "Повний текст тестової новини",
    }


# news_exists

def test_news_exists_true(db, news_data):
    db.add(NewsItem(**news_data))
    db.commit()

    assert news_exists(db, news_data["url"]) is True


def test_news_exists_false(db):
    assert news_exists(db, "https://example.com/unknown") is False


def test_news_exists_empty_url(db):
    assert news_exists(db, "") is False


# news_exists_by_title

def test_news_exists_by_title_true(db, news_data):
    db.add(NewsItem(**news_data))
    db.commit()

    assert news_exists_by_title(db, news_data["title"]) is True


def test_news_exists_by_title_false(db):
    assert news_exists_by_title(db, "Невідома новина") is False


def test_news_exists_by_title_empty(db):
    assert news_exists_by_title(db, "") is False


# create_news

def test_create_news(db, news_data):
    news = create_news(db, news_data)

    assert isinstance(news, NewsItem)
    assert news.title == news_data["title"]
    assert news.url == news_data["url"]
    assert news in db.new


# create_many_news

def test_create_many_news_saves_news(db):
    news_list = [
        {
            "title": "Новина 1",
            "url": "https://example.com/1",
            "summary": "Опис 1",
            "source": "Test",
            "published_at": "2026-11-11",
            "raw_text": "Текст 1",
        },
        {
            "title": "Новина 2",
            "url": "https://example.com/2",
            "summary": "Опис 2",
            "source": "Test",
            "published_at": "2026-11-11",
            "raw_text": "Текст 2",
        },
    ]

    result = create_many_news(db, news_list)

    assert result == {"saved": 2, "skipped": 0}
    assert db.query(NewsItem).count() == 2


def test_create_many_news_skips_duplicate_url(db, news_data):
    db.add(NewsItem(**news_data))
    db.commit()

    result = create_many_news(db, [news_data])

    assert result == {"saved": 0, "skipped": 1}
    assert db.query(NewsItem).count() == 1


def test_create_many_news_skips_duplicate_title(db, news_data):
    db.add(NewsItem(**news_data))
    db.commit()

    duplicate = {
        **news_data,
        "url": "https://example.com/another-url",
    }

    result = create_many_news(db, [duplicate])

    assert result == {"saved": 0, "skipped": 1}
    assert db.query(NewsItem).count() == 1


def test_create_many_news_skips_empty_title(db, news_data):
    invalid_news = {
        **news_data,
        "title": "",
    }

    result = create_many_news(db, [invalid_news])

    assert result == {"saved": 0, "skipped": 1}


def test_create_many_news_skips_empty_raw_text(db, news_data):
    invalid_news = {
        **news_data,
        "raw_text": "",
    }

    result = create_many_news(db, [invalid_news])

    assert result == {"saved": 0, "skipped": 1}


def test_create_many_news_empty_list(db):
    result = create_many_news(db, [])

    assert result == {"saved": 0, "skipped": 0}


def test_create_many_news_rollbacks_on_commit_error(
    db, news_data, monkeypatch
):
    def mock_commit():
        raise SQLAlchemyError("Помилка тестового commit")

    monkeypatch.setattr(db, "commit", mock_commit)

    result = create_many_news(db, [news_data])

    assert result == {"saved": 0, "skipped": 1}
    assert db.query(NewsItem).count() == 0
