
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app
from app import main
from app.api import endpoints
from app.models import NewsItem, Post, Source, Keyword


# Окрема тестова база даних
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


# Підміна обох залежностей get_db
@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[main.get_db] = override_get_db
    app.dependency_overrides[endpoints.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def news_data():
    return {
        "title": "Новина про Python",
        "url": "https://example.com/python",
        "summary": "Короткий опис новини",
        "source": "Test source",
        "published_at": "2026-11-11",
        "raw_text": "Вийшло нове оновлення Python для розробників.",
    }


# -------------------------
# GET /
# -------------------------

def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Наш проєкт працює!"
    }


# -------------------------
# POST /news
# -------------------------

def test_create_news_success(client, db, news_data, monkeypatch):
    monkeypatch.setattr(
        main,
        "matches_keywords",
        lambda title, text, keywords: True,
    )
    monkeypatch.setattr(
        main,
        "generate_post",
        lambda title, text: "Згенерований тестовий допис",
    )

    response = client.post("/news", json=news_data)

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Новину збережено, допис згенеровано"
    assert data["title"] == news_data["title"]
    assert data["generated_text"] == "Згенерований тестовий допис"
    assert data["status"] == "generated"

    assert db.query(NewsItem).count() == 1
    assert db.query(Post).count() == 1


def test_create_news_duplicate_url(client, db, news_data):
    db.add(NewsItem(**news_data))
    db.commit()

    response = client.post("/news", json=news_data)

    assert response.status_code == 409
    assert response.json()["detail"] == "Така новина вже є в базі"


def test_create_news_filtered(client, db, news_data, monkeypatch):
    monkeypatch.setattr(
        main,
        "matches_keywords",
        lambda title, text, keywords: False,
    )

    response = client.post("/news", json=news_data)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "filtered"
    assert data["news_id"] is not None
    assert db.query(NewsItem).count() == 1
    assert db.query(Post).count() == 0


def test_create_news_generation_error(
    client, db, news_data, monkeypatch
):
    monkeypatch.setattr(
        main,
        "matches_keywords",
        lambda title, text, keywords: True,
    )

    def mock_generate_post(title, text):
        raise Exception("Тестова помилка ШІ")

    monkeypatch.setattr(main, "generate_post", mock_generate_post)

    response = client.post("/news", json=news_data)

    assert response.status_code == 502
    assert "Не вдалося згенерувати допис" in response.json()["detail"]


def test_create_news_validation_error(client):
    response = client.post(
        "/news",
        json={"title": "Новина без обов'язкових полів"},
    )

    assert response.status_code == 422


# -------------------------
# GET /api/news/
# -------------------------

def test_get_news(client, db, news_data):
    db.add(NewsItem(**news_data))
    db.commit()

    response = client.get("/api/news/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == news_data["title"]


def test_get_news_empty(client):
    response = client.get("/api/news/")

    assert response.status_code == 200
    assert response.json() == []


# -------------------------
# GET /api/posts/
# -------------------------

def test_get_posts(client, db, news_data):
    news = NewsItem(**news_data)
    db.add(news)
    db.commit()
    db.refresh(news)

    post = Post(
        news_id=news.id,
        generated_text="Тестовий допис",
        status="generated",
    )
    db.add(post)
    db.commit()

    response = client.get("/api/posts/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["generated_text"] == "Тестовий допис"


def test_get_posts_empty(client):
    response = client.get("/api/posts/")

    assert response.status_code == 200
    assert response.json() == []


# -------------------------
# SOURCES
# -------------------------

def test_create_source(client, db):
    source_data = {
        "type": "site",
        "name": "Test site",
        "url": "https://example.com",
        "enabled": True,
    }

    response = client.post("/api/sources/", json=source_data)

    assert response.status_code == 200
    assert response.json()["name"] == "Test site"
    assert response.json()["enabled"] is True
    assert db.query(Source).count() == 1


def test_create_source_duplicate(client):
    source_data = {
        "type": "site",
        "name": "Test site",
        "url": "https://example.com",
        "enabled": True,
    }

    client.post("/api/sources/", json=source_data)
    response = client.post("/api/sources/", json=source_data)

    assert response.status_code == 409


def test_get_sources(client, db):
    db.add(
        Source(
            type="site",
            name="Test site",
            url="https://example.com",
            enabled=True,
        )
    )
    db.commit()

    response = client.get("/api/sources/")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_delete_source(client, db):
    source = Source(
        type="site",
        name="Test site",
        url="https://example.com",
        enabled=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    response = client.delete(f"/api/sources/{source.id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Джерело успішно видалено"
    assert db.query(Source).count() == 0


def test_delete_source_not_found(client):
    response = client.delete("/api/sources/999")

    assert response.status_code == 404


def test_update_source_enabled(client, db):
    source = Source(
        type="site",
        name="Test site",
        url="https://example.com",
        enabled=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    response = client.patch(
        f"/api/sources/{source.id}/enabled",
        json={"enabled": False},
    )

    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_update_source_not_found(client):
    response = client.patch(
        "/api/sources/999/enabled",
        json={"enabled": False},
    )

    assert response.status_code == 404


# -------------------------
# KEYWORDS
# -------------------------

def test_create_keyword(client, db):
    response = client.post(
        "/api/keywords/",
        json={"word": "Python"},
    )

    assert response.status_code == 200
    assert response.json()["word"] == "Python"
    assert db.query(Keyword).count() == 1


def test_get_keywords(client, db):
    db.add(Keyword(word="Python"))
    db.commit()

    response = client.get("/api/keywords/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["word"] == "Python"


def test_update_keyword(client, db):
    keyword = Keyword(word="Python")
    db.add(keyword)
    db.commit()
    db.refresh(keyword)

    response = client.put(
        f"/api/keywords/{keyword.id}",
        json={"word": "FastAPI"},
    )

    assert response.status_code == 200
    assert response.json()["word"] == "FastAPI"


def test_update_keyword_not_found(client):
    response = client.put(
        "/api/keywords/999",
        json={"word": "FastAPI"},
    )

    assert response.status_code == 404


def test_delete_keyword(client, db):
    keyword = Keyword(word="Python")
    db.add(keyword)
    db.commit()
    db.refresh(keyword)

    response = client.delete(f"/api/keywords/{keyword.id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Ключове слово успішно видалено"
    assert db.query(Keyword).count() == 0


def test_delete_keyword_not_found(client):
    response = client.delete("/api/keywords/999")

    assert response.status_code == 404


# -------------------------
# POST /api/generate/
# -------------------------

def test_generate_posts_endpoint(client, monkeypatch):
    class FakeTask:
        id = "test-task-id"

    def mock_delay():
        return FakeTask()

    monkeypatch.setattr(
        endpoints.generate_posts_for_news,
        "delay",
        mock_delay,
    )

    response = client.post("/api/generate/")

    assert response.status_code == 200
    assert response.json()["message"] == "Генерацію дописів запущено"
    assert response.json()["task_id"] == "test-task-id"
