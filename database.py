"""
Database moduli - SQLite
"""
import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.getenv("DATABASE_PATH", "german_mentor.db")


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def init_db():
    """Ma'lumotlar bazasini yaratish"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            level TEXT DEFAULT 'a1',
            xp INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            wrong TEXT,
            correct TEXT,
            context TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database tayyor")


def get_or_create_user(user_id, username=None, first_name=None, last_name=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        c.execute(
            "INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name)
        )
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()

    conn.close()
    cols = ["user_id", "username", "first_name", "last_name", "level", "xp", "created_at"]
    return dict(zip(cols, user))


def add_mistake(user_id, wrong, correct, context=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO mistakes (user_id, wrong, correct, context) VALUES (?, ?, ?, ?)",
        (user_id, wrong, correct, context)
    )
    conn.commit()
    conn.close()


def get_user_mistakes(user_id, limit=20):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT wrong, correct, context FROM mistakes WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = c.fetchall()
    conn.close()
    return [{"wrong": r[0], "correct": r[1], "context": r[2]} for r in rows]


def add_xp(user_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET xp = xp + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
