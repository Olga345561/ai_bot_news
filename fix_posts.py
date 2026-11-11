import sqlite3

connection = sqlite3.connect("ai_bot_news.db")

cursor = connection.cursor()

cursor.execute("""
    UPDATE post
    SET published_at = NULL
    WHERE status = 'generated'
    AND published_at IS NOT NULL
""")

connection.commit()

print("Виправлено записів:", cursor.rowcount)

connection.close()