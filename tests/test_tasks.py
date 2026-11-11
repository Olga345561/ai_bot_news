import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock, patch

from app.database import Base
from app.models import NewsItem, Post, Keyword, Source
import app.tasks as tasks_module

from app.tasks import (
    generate_posts_for_news,
    publish_generated_posts,
    run_news_pipeline
)

def create_test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )

    Base.metadata.create_all(bind=engine)

    return TestingSessionLocal, engine


def add_test_data(db, title="Новина про Python", raw_text="Новий Python"):
    news = NewsItem(
        title=title,
        url="https://example.com/news",
        summary=raw_text,
        source="Test",
        published_at="2026-11-11",
        raw_text=raw_text
    )

    keyword = Keyword(word="Python")

    db.add_all([news, keyword])
    db.commit()

    return news


@patch("app.tasks.SessionLocal")
@patch("app.tasks.generate_post")
@patch("app.tasks.matches_keywords")
def test_generate_posts_success(
    mock_matches,
    mock_generate,
    mock_session_local
):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()
    mock_session_local.return_value = db

    try:
        news = add_test_data(db)

        mock_matches.return_value = True
        mock_generate.return_value = "Новий допис про Python 🐍"

        result = generate_posts_for_news.run()

        assert result == {
            "generated": 1,
            "skipped": 0,
            "errors": 0
        }

        post = db.query(Post).filter(
            Post.news_id == news.id
        ).first()

        assert post is not None
        assert post.generated_text == "Новий допис про Python 🐍"
        assert post.status == "generated"

    finally:
        db.close()
        engine.dispose()


@patch("app.tasks.SessionLocal")
@patch("app.tasks.matches_keywords")
def test_generate_posts_keyword_not_matched(
    mock_matches,
    mock_session_local
):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()
    mock_session_local.return_value = db

    try:
        add_test_data(db)

        mock_matches.return_value = False

        result = generate_posts_for_news.run()

        assert result == {
            "generated": 0,
            "skipped": 1,
            "errors": 0
        }

        assert db.query(Post).count() == 0

    finally:
        db.close()
        engine.dispose()


@patch("app.tasks.SessionLocal")
@patch("app.tasks.generate_post")
@patch("app.tasks.matches_keywords")
def test_generate_posts_existing_post(
    mock_matches,
    mock_generate,
    mock_session_local
):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()
    mock_session_local.return_value = db

    try:
        news = add_test_data(db)

        db.add(Post(
            news_id=news.id,
            generated_text="Вже існуючий допис",
            status="generated"
        ))
        db.commit()

        result = generate_posts_for_news.run()

        assert result == {
            "generated": 0,
            "skipped": 1,
            "errors": 0
        }

        mock_generate.assert_not_called()

    finally:
        db.close()
        engine.dispose()


@patch("app.tasks.SessionLocal")
@patch("app.tasks.generate_post")
@patch("app.tasks.matches_keywords")
def test_generate_posts_ai_error(
    mock_matches,
    mock_generate,
    mock_session_local
):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()
    mock_session_local.return_value = db

    try:
        add_test_data(db)

        mock_matches.return_value = True
        mock_generate.side_effect = Exception("Помилка AI")

        result = generate_posts_for_news.run()

        assert result == {
            "generated": 0,
            "skipped": 0,
            "errors": 1
        }

        assert db.query(Post).count() == 0

    finally:
        db.close()
        engine.dispose()


# =====================================================
# Тести publish_generated_posts()
# =====================================================

def test_publish_generated_posts_no_posts(monkeypatch):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()

    monkeypatch.setattr(
        tasks_module,
        "SessionLocal",
        TestingSessionLocal
    )

    try:
        result = publish_generated_posts.run()

        assert result == {
            "message": "Немає дописів для публікації"
        }

        assert db.query(Post).count() == 0

    finally:
        db.close()
        engine.dispose()


def test_publish_generated_posts_success(monkeypatch):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()

    monkeypatch.setattr(
        tasks_module,
        "SessionLocal",
        TestingSessionLocal
    )

    mock_publish = AsyncMock(return_value={"ok": True})

    monkeypatch.setattr(
        tasks_module,
        "publish_post",
        mock_publish
    )

    try:
        news = add_test_data(db)

        post = Post(
            news_id=news.id,
            generated_text="Тестовий допис для Telegram",
            status="generated"
        )

        db.add(post)
        db.commit()

        result = publish_generated_posts.run()

        db.refresh(post)

        assert result == {
            "message": "Допис опубліковано",
            "post_id": post.id
        }

        assert post.status == "published"
        assert post.published_at is not None

        mock_publish.assert_awaited_once_with(
            "Тестовий допис для Telegram"
        )

    finally:
        db.close()
        engine.dispose()


def test_publish_generated_posts_not_confirmed(monkeypatch):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()

    monkeypatch.setattr(
        tasks_module,
        "SessionLocal",
        TestingSessionLocal
    )

    mock_publish = AsyncMock(return_value={"ok": False})

    monkeypatch.setattr(
        tasks_module,
        "publish_post",
        mock_publish
    )

    try:
        news = add_test_data(db)

        post = Post(
            news_id=news.id,
            generated_text="Тестовий допис",
            status="generated"
        )

        db.add(post)
        db.commit()

        result = publish_generated_posts.run()

        db.refresh(post)

        assert result == {
            "message": "Telegram не підтвердив публікацію"
        }

        # Допис залишається доступним для повторної публікації
        assert post.status == "generated"

        mock_publish.assert_awaited_once()

    finally:
        db.close()
        engine.dispose()


def test_publish_generated_posts_error_restores_status(monkeypatch):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()

    monkeypatch.setattr(
        tasks_module,
        "SessionLocal",
        TestingSessionLocal
    )

    mock_publish = AsyncMock(
        side_effect=Exception("Помилка Telegram")
    )

    monkeypatch.setattr(
        tasks_module,
        "publish_post",
        mock_publish
    )

    try:
        news = add_test_data(db)

        post = Post(
            news_id=news.id,
            generated_text="Тестовий допис",
            status="generated"
        )

        db.add(post)
        db.commit()

        post_id = post.id

        # Перевіряємо, що помилка передається далі
        with pytest.raises(Exception, match="Помилка Telegram"):
            publish_generated_posts.run()

        db.expire_all()

        post = db.query(Post).filter(
            Post.id == post_id
        ).first()

        # Після помилки статус має відновитися
        assert post.status == "generated"

        mock_publish.assert_awaited_once()

    finally:
        db.close()
        engine.dispose()


# =====================================================
# Тести run_news_pipeline()
# =====================================================

def test_run_news_pipeline_no_active_sources(monkeypatch):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()

    monkeypatch.setattr(
        tasks_module,
        "SessionLocal",
        TestingSessionLocal
    )

    mock_chain = MagicMock()

    monkeypatch.setattr(
        tasks_module,
        "chain",
        mock_chain
    )

    try:
        result = run_news_pipeline.run()

        assert result == {
            "message": "Немає активних джерел для обробки"
        }

        # Ланцюжок завдань не повинен запускатися
        mock_chain.assert_not_called()

    finally:
        db.close()
        engine.dispose()


def test_run_news_pipeline_starts_chain(monkeypatch):
    TestingSessionLocal, engine = create_test_db()
    db = TestingSessionLocal()

    monkeypatch.setattr(
        tasks_module,
        "SessionLocal",
        TestingSessionLocal
    )

    mock_chain = MagicMock()
    mock_workflow = MagicMock()
    mock_result = MagicMock()

    mock_result.id = "test-task-123"

    mock_workflow.apply_async.return_value = mock_result
    mock_chain.return_value = mock_workflow

    monkeypatch.setattr(
        tasks_module,
        "chain",
        mock_chain
    )

    try:
        # Створюємо два активних джерела різних типів
        site_source = Source(
            type="site",
            name="Тестовий сайт",
            url="https://example.com",
            enabled=True
        )

        telegram_source = Source(
            type="telegram",
            name="Тестовий Telegram",
            url="test_channel",
            enabled=True
        )

        db.add_all([site_source, telegram_source])
        db.commit()

        result = run_news_pipeline.run()

        assert result == {
            "message": "Обробку новин запущено",
            "task_id": "test-task-123"
        }

        # Два джерела + генерація + публікація
        mock_chain.assert_called_once()

        pipeline_tasks = mock_chain.call_args.args

        assert len(pipeline_tasks) == 4

        # Перевіряємо, що Celery отримав команду запуску
        mock_workflow.apply_async.assert_called_once()

    finally:
        db.close()
        engine.dispose()
