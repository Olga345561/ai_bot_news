
import pytest

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import NewsItem, Post, Source, Keyword


# Створюємо окрему тестову базу даних у пам'яті
@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Увімкнення перевірки зовнішніх ключів SQLite
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


# Допоміжна функція для створення тестової новини
def create_test_news(db, url="https://example.com/news-1"):
    news = NewsItem(
        title="Тестова новина",
        url=url,
        summary="Короткий опис новини",
        source="Test source",
        published_at="2026-11-11",
        raw_text="Текст тестової новини",
    )
    db.add(news)
    db.commit()
    return news


# -------------------------
# NEWS ITEM
# -------------------------

def test_create_news_item(db_session):
    news = create_test_news(db_session)

    assert news.id is not None
    assert news.title == "Тестова новина"
    assert news.source == "Test source"


@pytest.mark.parametrize(
    "missing_field",
    ["title", "summary", "source", "published_at", "raw_text"],
)
def test_news_item_required_fields(db_session, missing_field):
    data = {
        "title": "Тестова новина",
        "url": "https://example.com/news",
        "summary": "Опис",
        "source": "Test source",
        "published_at": "2026-11-11",
        "raw_text": "Текст новини",
    }

    data.pop(missing_field)

    db_session.add(NewsItem(**data))

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_news_item_url_can_be_null(db_session):
    news = NewsItem(
        title="Новина без URL",
        url=None,
        summary="Опис",
        source="Test source",
        published_at="2026-11-11",
        raw_text="Текст",
    )

    db_session.add(news)
    db_session.commit()

    assert news.id is not None
    assert news.url is None


def test_news_item_url_must_be_unique(db_session):
    create_test_news(db_session)

    duplicate = NewsItem(
        title="Інша новина",
        url="https://example.com/news-1",
        summary="Інший опис",
        source="Test source",
        published_at="2026-11-11",
        raw_text="Інший текст",
    )

    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


# -------------------------
# POST
# -------------------------

def test_create_post(db_session):
    news = create_test_news(db_session)

    post = Post(
        news_id=news.id,
        generated_text="Тестовий допис",
        status="generated",
    )

    db_session.add(post)
    db_session.commit()

    assert post.id is not None
    assert post.news_id == news.id
    assert post.status == "generated"
    assert post.published_at is None


def test_post_news_id_must_reference_existing_news(db_session):
    post = Post(
        news_id=999,
        generated_text="Тестовий допис",
        status="generated",
    )

    db_session.add(post)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_post_news_id_must_be_unique(db_session):
    news = create_test_news(db_session)

    post1 = Post(
        news_id=news.id,
        generated_text="Перший допис",
        status="generated",
    )

    db_session.add(post1)
    db_session.commit()

    post2 = Post(
        news_id=news.id,
        generated_text="Другий допис",
        status="generated",
    )

    db_session.add(post2)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    "missing_field",
    ["news_id", "generated_text", "status"],
)
def test_post_required_fields(db_session, missing_field):
    news = create_test_news(db_session)

    data = {
        "news_id": news.id,
        "generated_text": "Тестовий допис",
        "status": "generated",
    }

    data.pop(missing_field)

    db_session.add(Post(**data))

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


# -------------------------
# SOURCE
# -------------------------

def test_create_source(db_session):
    source = Source(
        type="site",
        name="Highload",
        url="https://highload.tech/",
    )

    db_session.add(source)
    db_session.commit()

    assert source.id is not None
    assert source.type == "site"
    assert source.enabled is True


def test_source_name_and_url_can_be_null(db_session):
    source = Source(
        type="telegram",
        name=None,
        url=None,
    )

    db_session.add(source)
    db_session.commit()

    assert source.id is not None
    assert source.name is None
    assert source.url is None


def test_source_type_is_required(db_session):
    source = Source(
        name="Highload",
        url="https://highload.tech/",
    )

    db_session.add(source)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


# -------------------------
# KEYWORD
# -------------------------

def test_create_keyword(db_session):
    keyword = Keyword(word="Python")

    db_session.add(keyword)
    db_session.commit()

    assert keyword.id is not None
    assert keyword.word == "Python"


def test_keyword_word_must_be_unique(db_session):
    keyword1 = Keyword(word="Python")
    db_session.add(keyword1)
    db_session.commit()

    keyword2 = Keyword(word="Python")
    db_session.add(keyword2)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_keyword_word_is_required(db_session):
    keyword = Keyword()

    db_session.add(keyword)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
