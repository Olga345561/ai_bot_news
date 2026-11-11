import sqlite3

connection = sqlite3.connect("ai_bot_news.db")

try:
    connection.execute("PRAGMA foreign_keys = OFF")

    connection.execute("""
        CREATE TABLE post_new (
            id INTEGER PRIMARY KEY,
            news_id INTEGER NOT NULL,
            generated_text VARCHAR NOT NULL,
            published_at VARCHAR,
            status VARCHAR NOT NULL,
            FOREIGN KEY (news_id) REFERENCES news_item(id)
        )
    """)

    connection.execute("""
        INSERT INTO post_new (
            id,
            news_id,
            generated_text,
            published_at,
            status
        )
        SELECT
            id,
            news_id,
            generated_text,
            published_at,
            status
        FROM post
    """)

    connection.execute("DROP TABLE post")
    connection.execute("ALTER TABLE post_new RENAME TO post")

    connection.commit()

    print("Міграція успішна!")

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()