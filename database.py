import sqlite3

DB_PATH = "events.db"


def init_db():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                due TEXT NOT NULL,
                reminder_time TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reminded INTEGER NOT NULL DEFAULT 0
            )
        """)
        connection.commit()


def add_event(guild_id, title, due, reminder_time, channel_id, user_id):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            INSERT INTO events
            (guild_id, title, due, reminder_time, channel_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                title,
                due.isoformat(),
                reminder_time.isoformat(),
                channel_id,
                user_id,
            ),
        )
        connection.commit()
        return cursor.lastrowid


def get_events(guild_id):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT *
            FROM events
            WHERE guild_id = ?
            ORDER BY due
            """,
            (guild_id,),
        ).fetchall()


def get_due_events():
    from datetime import datetime

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT *
            FROM events
            WHERE reminded = 0 AND reminder_time <= ?
            """,
            (datetime.now().isoformat(),),
        ).fetchall()


def delete_event(event_id, guild_id):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "DELETE FROM events WHERE id = ? AND guild_id = ?",
            (event_id, guild_id),
        )
        connection.commit()


def mark_reminded(event_id):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "UPDATE events SET reminded = 1 WHERE id = ?",
            (event_id,),
        )
        connection.commit()