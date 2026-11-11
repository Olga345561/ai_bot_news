
import asyncio
import logging
from datetime import datetime, timezone

from celery import chain
from sqlalchemy import update

from celery_worker import celery_app
from app.database import SessionLocal
from app.news_parser.sites import fetch_and_save_news
from app.news_parser.telegram import main as parse_telegram
from app.models import Post, NewsItem, Keyword, Source
from app.telegram.publisher import publish_post
from app.utils import matches_keywords
from app.ai.generator import generate_post


logger = logging.getLogger(__name__)


@celery_app.task
def parse_site_news(source: str, base_url: str):
    db = SessionLocal()

    try:
        logger.info(
            "Початок задачі парсингу сайту: source=%s, url=%s",
            source,
            base_url
        )

        result = fetch_and_save_news(
            db,
            source=source,
            base_url=base_url
        )

        logger.info(
            "Парсинг сайту завершено: source=%s, result=%s",
            source,
            result
        )

        return result

    except Exception:
        logger.exception(
            "Помилка парсингу сайту: source=%s",
            source
        )
        raise

    finally:
        db.close()


@celery_app.task
def parse_telegram_news(channel: str, source: str, limit: int = 30):
    try:
        logger.info(
            "Початок задачі парсингу Telegram: channel=%s, limit=%s",
            channel,
            limit
        )

        result = asyncio.run(
            parse_telegram(
                channel=channel,
                source=source,
                limit=limit
            )
        )

        logger.info(
            "Парсинг Telegram завершено: channel=%s, result=%s",
            channel,
            result
        )

        return result

    except Exception:
        logger.exception(
            "Помилка парсингу Telegram: channel=%s",
            channel
        )
        raise


@celery_app.task
def publish_generated_posts():
    db = SessionLocal()

    try:
        logger.info("Початок задачі публікації дописів")

        # Знаходимо ID першого допису для публікації
        post_id = db.query(Post.id).filter(
            Post.status == "generated"
        ).order_by(Post.id).first()

        if not post_id:
            logger.info("Немає дописів для публікації")
            return {"message": "Немає дописів для публікації"}

        post_id = post_id[0]

        # Атомарно резервуємо допис.
        # Лише один Worker зможе змінити generated на publishing.
        claim = db.execute(
            update(Post)
            .where(
                Post.id == post_id,
                Post.status == "generated"
            )
            .values(status="publishing")
        )

        db.commit()

        if claim.rowcount != 1:
            logger.warning(
                "Допис уже обробляється іншою задачею: post_id=%s",
                post_id
            )
            return {"message": "Допис уже обробляється іншою задачею"}

        post = db.query(Post).filter(Post.id == post_id).first()

        try:
            result = asyncio.run(
                publish_post(post.generated_text)
            )

            if result.get("ok"):
                post.status = "published"
                post.published_at = datetime.now(timezone.utc).isoformat()
                db.commit()

                logger.info(
                    "Пост успішно опубліковано: post_id=%s",
                    post_id
                )

                return {
                    "message": "Допис опубліковано",
                    "post_id": post_id
                }

            post.status = "generated"
            db.commit()

            logger.warning(
                "Telegram не підтвердив публікацію: post_id=%s",
                post_id
            )

            return {"message": "Telegram не підтвердив публікацію"}

        except Exception:
            db.rollback()

            db.query(Post).filter(
                Post.id == post_id,
                Post.status == "publishing"
            ).update({"status": "generated"})

            db.commit()

            logger.exception(
                "Помилка публікації поста: post_id=%s",
                post_id
            )

            raise

    except Exception:
        logger.exception(
            "Помилка виконання задачі публікації"
        )
        raise

    finally:
        db.close()


@celery_app.task
def generate_posts_for_news():
    db = SessionLocal()

    generated = 0
    skipped = 0
    errors = 0

    try:
        news_items = db.query(NewsItem).all()
        keywords = db.query(Keyword).all()
        keyword_words = [keyword.word for keyword in keywords]

        logger.info(
            "Початок генерації: новин=%s, ключових слів=%s",
            len(news_items),
            len(keyword_words)
        )

        for news in news_items:
            try:
                # Перевіряємо, чи вже є допис для цієї новини
                existing_post = db.query(Post).filter(
                    Post.news_id == news.id
                ).first()

                if existing_post:
                    skipped += 1
                    continue

                # Перевіряємо ключові слова
                if not matches_keywords(
                    news.title,
                    news.raw_text,
                    keyword_words
                ):
                    skipped += 1
                    continue

                # Генеруємо допис за допомогою ШІ
                generated_text = generate_post(
                    news.title,
                    news.raw_text
                )

                if not generated_text or not generated_text.strip():
                    errors += 1

                    logger.warning(
                        "ШІ повернув порожній текст: news_id=%s",
                        news.id
                    )
                    continue

                # Створюємо допис
                db_post = Post(
                    news_id=news.id,
                    generated_text=generated_text,
                    status="generated"
                )

                db.add(db_post)
                db.commit()

                generated += 1

                logger.info(
                    "Допис успішно згенеровано: news_id=%s, post_id=%s",
                    news.id,
                    db_post.id
                )

            except Exception:
                db.rollback()
                errors += 1

                logger.exception(
                    "Помилка генерації допису: news_id=%s",
                    news.id
                )

        logger.info(
            "Генерацію завершено: generated=%s, skipped=%s, errors=%s",
            generated,
            skipped,
            errors
        )

        return {
            "generated": generated,
            "skipped": skipped,
            "errors": errors
        }

    except Exception:
        logger.exception("Помилка виконання задачі генерації дописів")
        raise

    finally:
        db.close()


@celery_app.task
def run_news_pipeline():
    db = SessionLocal()

    try:
        # Отримуємо активні джерела з бази даних
        sources = db.query(Source).filter(
            Source.enabled == True
        ).all()

        logger.info(
            "Знайдено активних джерел: %s",
            len(sources)
        )

        pipeline_tasks = []

        for source in sources:

            if not source.url:
                logger.warning(
                    "Пропущено джерело без URL: source_id=%s",
                    source.id
                )
                continue

            if source.type == "site":
                task = parse_site_news.si(
                    source.name or source.url,
                    source.url
                )
                pipeline_tasks.append(task)

            elif source.type == "telegram":
                task = parse_telegram_news.si(
                    source.url,
                    source.name or source.url,
                    30
                )
                pipeline_tasks.append(task)

            else:
                logger.warning(
                    "Невідомий тип джерела: source_id=%s, type=%s",
                    source.id,
                    source.type
                )

        if not pipeline_tasks:
            logger.warning("Немає активних джерел для обробки")
            return {
                "message": "Немає активних джерел для обробки"
            }

    except Exception:
        logger.exception("Помилка під час отримання джерел")
        raise

    finally:
        db.close()

    # Додаємо генерацію дописів
    pipeline_tasks.append(generate_posts_for_news.si())

    # Додаємо публікацію
    pipeline_tasks.append(publish_generated_posts.si())

    try:
        workflow = chain(*pipeline_tasks)

        result = workflow.apply_async()

        logger.info(
            "Запущено обробку новин: task_id=%s",
            result.id
        )

        return {
            "message": "Обробку новин запущено",
            "task_id": result.id
        }

    except Exception:
        logger.exception("Не вдалося запустити обробку новин")
        raise
