"""SQLite storage for the Planner bot: creates the events table and saves, 
lists, deletes, and flags reminders for assignments."""
from datetime import datetime
import sqlite3

DB_PATH = "events.db"


def init_db():
    """Create the events table in the database if it does not already exist."""
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


def add_event(guild_id, title, due, reminder_time, channel_id, user_id): # pylint: disable=too-many-arguments,too-many-positional-arguments
    """add event to database"""
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
    """Return all stored assignments for one server.

    Args:
        guild_id: ID of the Discord server to look up.

    Returns:
        A list of that server's assignments.
    """
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
    """Return assignments whose reminder time has arrived and have not been reminded yet.

    Returns:
        A list of assignments that need a reminder sent.
    """
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
    """Remove an assignment from one server.

    Args:
        event_id: ID of the assignment to delete.
        guild_id: ID of the server, so only that server's data is affected.
    """
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "DELETE FROM events WHERE id = ? AND guild_id = ?",
            (event_id, guild_id),
        )
        connection.commit()


def mark_reminded(event_id):
    """Mark an assignment as reminded so it is not reminded again.

    Args:
        event_id: ID of the assignment that was reminded.
    """
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "UPDATE events SET reminded = 1 WHERE id = ?",
            (event_id,),
        )
        connection.commit()
