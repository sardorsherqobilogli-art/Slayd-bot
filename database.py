#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - SQLite Ma'lumotlar Bazasi
YANGILANGAN VERSION - Lug'at, Sayfa, Kitob Materiallar jadvallari bilan
"""

import sqlite3
import json
import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from config import logger, DATABASE_PATH, XP_REWARDS, LEVEL_REQUIREMENTS


class Database:
    """Asosiy ma'lumotlar bazasi klassi"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_database(self):
        """Barcha jadvallarni yaratadi"""
        with self._connect() as conn:
            cursor = conn.cursor()

            # 1. Foydalanuvchilar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    current_level TEXT DEFAULT 'a1',
                    target_level TEXT DEFAULT 'c1',
                    total_xp INTEGER DEFAULT 0,
                    streak_days INTEGER DEFAULT 0,
                    last_active TEXT,
                    joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    voice_preference TEXT DEFAULT 'female',
                    tts_speed REAL DEFAULT 1.0,
                    show_mistakes INTEGER DEFAULT 1,
                    ai_difficulty TEXT DEFAULT 'adaptive',
                    speaking_score REAL DEFAULT 0.0,
                    current_lektion INTEGER DEFAULT 1,
                    total_conversations INTEGER DEFAULT 0,
                    phone TEXT,
                    channel_subscribed INTEGER DEFAULT 0
                )
            """)

            # 2. Xatolar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mistakes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_input TEXT,
                    correct_form TEXT,
                    mistake_type TEXT,
                    mini_lesson TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT,
                    mastered INTEGER DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 3. Progress jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    xp_amount INTEGER,
                    activity_type TEXT,
                    activity_detail TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 4. Kunlik so'zlar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    german TEXT,
                    uzbek TEXT,
                    izoh TEXT,
                    misol TEXT,
                    sinonimlar TEXT,
                    date TEXT,
                    learned INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 5. Suhbatlar tarixi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    topic TEXT,
                    messages TEXT,
                    score INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # ==================== YANGI JADVALLAR ====================

            # 6. Lug'at kitoblari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lugat_books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 7. Lug'at bo'limlari (chapters)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lugat_chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    order_num INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES lugat_books(id)
                )
            """)

            # 8. Lug'at so'zlari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lugat_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter_id INTEGER,
                    german TEXT NOT NULL,
                    uzbek TEXT NOT NULL,
                    izoh TEXT,
                    sinonimlar TEXT,
                    order_num INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chapter_id) REFERENCES lugat_chapters(id)
                )
            """)

            # 9. Sayfa materiallari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sayfa_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_key TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    pdf_path TEXT,
                    audio_path TEXT,
                    order_num INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 10. Kitob materiallari (Kitob Materiallar bo'limi)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kitob_books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    author TEXT,
                    cover_image TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 11. Kitob materiallari fayllari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kitob_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    file_path TEXT NOT NULL,
                    type TEXT DEFAULT 'pdf',
                    order_num INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES kitob_books(id)
                )
            """)

            conn.commit()
            logger.info("Barcha jadvallar yaratildi!")

    # ==================== USERS ====================

    def get_or_create_user(self, user_id: int, username=None, first_name=None, last_name=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()

            if not user:
                cursor.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, last_active)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, datetime.datetime.now().isoformat()))
                conn.commit()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user = cursor.fetchone()
            else:
                cursor.execute("UPDATE users SET last_active = ? WHERE user_id = ?",
                               (datetime.datetime.now().isoformat(), user_id))
                conn.commit()

            return dict(user) if user else {}

    def update_user(self, user_id: int, **kwargs):
        with self._connect() as conn:
            cursor = conn.cursor()
            for key, value in kwargs.items():
                cursor.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
            conn.commit()

    def get_user(self, user_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}

    # ==================== XP ====================

    def add_xp(self, user_id: int, amount: int, activity_type: str, detail: str = ""):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO progress (user_id, xp_amount, activity_type, activity_detail) VALUES (?, ?, ?, ?)",
                           (user_id, amount, activity_type, detail))
            cursor.execute("UPDATE users SET total_xp = total_xp + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()

    def get_total_xp(self, user_id: int) -> int:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_xp FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

    # ==================== MISTAKES ====================

    def add_mistake(self, user_id: int, user_input: str, correct_form: str, mistake_type: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mistakes (user_id, user_input, correct_form, mistake_type)
                VALUES (?, ?, ?, ?)
            """, (user_id, user_input, correct_form, mistake_type))
            conn.commit()

    def get_mistakes(self, user_id: int, mastered: bool = False, limit: int = 10):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM mistakes WHERE user_id = ? AND mastered = ? ORDER BY created_at DESC LIMIT ?
            """, (user_id, 1 if mastered else 0, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_mistake_by_id(self, mistake_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mistakes WHERE id = ?", (mistake_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_mistake_stats(self, user_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM mistakes WHERE user_id = ? AND mastered = 0", (user_id,))
            active = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mistakes WHERE user_id = ? AND mastered = 1", (user_id,))
            mastered = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mistakes WHERE user_id = ?", (user_id,))
            total = cursor.fetchone()[0]
            return {"active": active, "mastered": mastered, "total": total}

    def master_mistake(self, mistake_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE mistakes SET mastered = 1, reviewed_at = ? WHERE id = ?",
                           (datetime.datetime.now().isoformat(), mistake_id))
            conn.commit()

    def review_mistake(self, mistake_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE mistakes SET review_count = review_count + 1, reviewed_at = ? WHERE id = ?",
                           (datetime.datetime.now().isoformat(), mistake_id))
            conn.commit()

    # ==================== DAILY WORDS ====================

    def get_daily_word(self, user_id: int):
        today = datetime.date.today().isoformat()
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_words WHERE user_id = ? AND date = ?", (user_id, today))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def save_daily_word(self, user_id: int, word: dict):
        today = datetime.date.today().isoformat()
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_words (user_id, german, uzbek, izoh, misol, sinonimlar, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, word.get("german", ""), word.get("uzbek", ""),
                  word.get("izoh", ""), word.get("misol", ""),
                  json.dumps(word.get("sinonimlar", [])), today))
            conn.commit()

    # ==================== LUG'AT BOOKS ====================

    def add_lugat_book(self, level: str, name: str, description: str = "") -> int:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO lugat_books (level, name, description) VALUES (?, ?, ?)",
                           (level, name, description))
            conn.commit()
            return cursor.lastrowid

    def get_lugat_books(self, level: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_books WHERE level = ? ORDER BY id", (level,))
            return [dict(row) for row in cursor.fetchall()]

    def get_lugat_book_by_id(self, book_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== LUG'AT CHAPTERS ====================

    def add_lugat_chapter(self, book_id: int, name: str, description: str = "", order_num: int = 0) -> int:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO lugat_chapters (book_id, name, description, order_num) VALUES (?, ?, ?, ?)",
                           (book_id, name, description, order_num))
            conn.commit()
            return cursor.lastrowid

    def get_lugat_chapters(self, book_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_chapters WHERE book_id = ? ORDER BY order_num", (book_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_lugat_chapter_by_id(self, chapter_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_chapters WHERE id = ?", (chapter_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== LUG'AT WORDS ====================

    def add_lugat_word(self, chapter_id: int, german: str, uzbek: str, izoh: str = "", sinonimlar: str = "", order_num: int = 0):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lugat_words (chapter_id, german, uzbek, izoh, sinonimlar, order_num)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chapter_id, german, uzbek, izoh, sinonimlar, order_num))
            conn.commit()

    def get_lugat_words(self, chapter_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_words WHERE chapter_id = ? ORDER BY order_num", (chapter_id,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== SAYFA MATERIALS ====================

    def add_sayfa_material(self, book_key: str, name: str, description: str = "", pdf_path: str = "", audio_path: str = "", order_num: int = 0) -> int:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sayfa_materials (book_key, name, description, pdf_path, audio_path, order_num)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (book_key, name, description, pdf_path, audio_path, order_num))
            conn.commit()
            return cursor.lastrowid

    def get_sayfa_materials(self, book_key: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sayfa_materials WHERE book_key = ? ORDER BY order_num", (book_key,))
            return [dict(row) for row in cursor.fetchall()]

    def get_sayfa_material_by_id(self, mat_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sayfa_materials WHERE id = ?", (mat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== KITOB BOOKS ====================

    def add_kitob_book(self, level: str, name: str, description: str = "", author: str = "", cover_image: str = "") -> int:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO kitob_books (level, name, description, author, cover_image)
                VALUES (?, ?, ?, ?, ?)
            """, (level, name, description, author, cover_image))
            conn.commit()
            return cursor.lastrowid

    def get_kitob_books(self, level: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kitob_books WHERE level = ? ORDER BY id", (level,))
            return [dict(row) for row in cursor.fetchall()]

    def get_kitob_book_by_id(self, book_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kitob_books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== KITOB MATERIALS ====================

    def add_kitob_material(self, book_id: int, name: str, file_path: str, description: str = "", type: str = "pdf", order_num: int = 0) -> int:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO kitob_materials (book_id, name, description, file_path, type, order_num)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (book_id, name, description, file_path, type, order_num))
            conn.commit()
            return cursor.lastrowid

    def get_kitob_materials(self, book_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kitob_materials WHERE book_id = ? ORDER BY order_num", (book_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_kitob_material_by_id(self, mat_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kitob_materials WHERE id = ?", (mat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


# Singleton
_db_instance = None

def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
