#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - SQLite Ma'lumotlar Bazasi
Foydalanuvchilar, xatolar, progress, kunlik vazifalar
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
                    total_flashcards INTEGER DEFAULT 0,
                    total_pomodoro_minutes INTEGER DEFAULT 0,
                    words_learned INTEGER DEFAULT 0
                )
            """)

            # 2. Xatolar banki (har bir xato + mini-dars)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mistakes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_input TEXT NOT NULL,
                    correct_form TEXT NOT NULL,
                    mistake_type TEXT NOT NULL,
                    grammar_rule TEXT,
                    mini_lesson TEXT,
                    practice_exercises TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    reviewed_count INTEGER DEFAULT 0,
                    last_reviewed TEXT,
                    is_mastered INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 3. Kunlik vazifalar
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_missions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT NOT NULL,
                    mission_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    target_count INTEGER DEFAULT 1,
                    current_count INTEGER DEFAULT 0,
                    xp_reward INTEGER DEFAULT 50,
                    is_completed INTEGER DEFAULT 0,
                    completed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 4. Speaking bali (har bir suhbatdan keyin)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS speaking_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_type TEXT NOT NULL,
                    topic TEXT,
                    score REAL NOT NULL,
                    feedback TEXT,
                    words_used TEXT,
                    grammar_errors TEXT,
                    duration_seconds INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 5. Lektsiya progressi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lektion_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    level TEXT NOT NULL,
                    book TEXT NOT NULL,
                    lektion_number INTEGER NOT NULL,
                    is_completed INTEGER DEFAULT 0,
                    flashcard_score REAL DEFAULT 0,
                    words_learned INTEGER DEFAULT 0,
                    completed_at TEXT,
                    UNIQUE(user_id, level, book, lektion_number)
                )
            """)

            # 6. XP tarixi (level up va barcha XP o'zgarishlari)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS xp_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 7. Voice vocab practice (ovozli lug'at mashqlari)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voice_practice (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    german_word TEXT NOT NULL,
                    user_pronunciation TEXT,
                    accuracy_score REAL DEFAULT 0,
                    feedback TEXT,
                    practiced_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 8. AI suhbatlari tarixi (Kontext AI uchun)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_type TEXT NOT NULL,
                    topic TEXT,
                    messages TEXT NOT NULL,
                    words_learned_today TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            logger.info("✅ Ma'lumotlar bazasi jadvallari tayyor!")

    # ==================== USERS ====================

    def get_or_create_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Foydalanuvchini olish yoki yaratish"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if row:
                # Mavjud user - faqat last_active ni yangilash
                cursor.execute(
                    "UPDATE users SET last_active = ? WHERE user_id = ?",
                    (datetime.datetime.now().isoformat(), user_id)
                )
                return dict(row)

            # Yangi user yaratish
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, last_active)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                kwargs.get("username", ""),
                kwargs.get("first_name", ""),
                kwargs.get("last_name", ""),
                datetime.datetime.now().isoformat(),
            ))

            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())

    def update_user(self, user_id: int, **fields) -> bool:
        """Foydalanuvchi ma'lumotlarini yangilash"""
        allowed = [
            "current_level", "target_level", "voice_preference", "tts_speed",
            "show_mistakes", "ai_difficulty", "speaking_score", "current_lektion",
            "total_conversations", "total_flashcards", "total_pomodoro_minutes",
            "words_learned", "streak_days", "total_xp",
        ]
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False

        with self._connect() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [user_id]
            cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
            return cursor.rowcount > 0

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Foydalanuvchi statistikasi"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return {}

            stats = dict(user)

            # Xatolar soni
            cursor.execute(
                "SELECT COUNT(*) as count FROM mistakes WHERE user_id = ? AND is_mastered = 0",
                (user_id,)
            )
            stats["active_mistakes"] = cursor.fetchone()["count"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM mistakes WHERE user_id = ? AND is_mastered = 1",
                (user_id,)
            )
            stats["mastered_mistakes"] = cursor.fetchone()["count"]

            # Kunlik vazifalar
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) as count FROM daily_missions WHERE user_id = ? AND date = ? AND is_completed = 1",
                (user_id, today)
            )
            stats["completed_missions_today"] = cursor.fetchone()["count"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM daily_missions WHERE user_id = ? AND date = ?",
                (user_id, today)
            )
            stats["total_missions_today"] = cursor.fetchone()["count"]

            # Lektsiya progressi
            cursor.execute(
                "SELECT COUNT(*) as count FROM lektion_progress WHERE user_id = ? AND is_completed = 1",
                (user_id,)
            )
            stats["completed_lektions"] = cursor.fetchone()["count"]

            return stats

    # ==================== XP SYSTEM ====================

    def add_xp(self, user_id: int, amount: int, reason: str, details: str = "") -> int:
        """XP qo'shish va tarixga yozish"""
        with self._connect() as conn:
            cursor = conn.cursor()

            # XP qo'shish
            cursor.execute(
                "UPDATE users SET total_xp = total_xp + ? WHERE user_id = ?",
                (amount, user_id)
            )

            # Tarixga yozish
            cursor.execute("""
                INSERT INTO xp_history (user_id, amount, reason, details, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, amount, reason, details, datetime.datetime.now().isoformat()))

            # Yangi total_xp ni olish
            cursor.execute("SELECT total_xp FROM users WHERE user_id = ?", (user_id,))
            new_total = cursor.fetchone()["total_xp"]
            return new_total

    def get_xp_history(self, user_id: int, days: int = 7) -> List[Dict]:
        """So'nggi N kunlik XP tarixi"""
        with self._connect() as conn:
            cursor = conn.cursor()
            since = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT * FROM xp_history
                WHERE user_id = ? AND created_at > ?
                ORDER BY created_at DESC
            """, (user_id, since))
            return [dict(row) for row in cursor.fetchall()]

    def check_level_up(self, user_id: int) -> Optional[str]:
        """Daraja o'tish mumkinligini tekshirish, yangi darajani qaytaradi yoki None"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return None

            current_level = user["current_level"]
            total_xp = user["total_xp"]
            speaking_score = user["speaking_score"]

            # Keyingi darajani aniqlash
            level_order = ["a1", "a2", "b1", "b2", "c1"]
            try:
                current_idx = level_order.index(current_level)
                if current_idx >= len(level_order) - 1:
                    return None  # C1 - eng yuqori daraja
                next_level = level_order[current_idx + 1]
            except ValueError:
                return None

            reqs = LEVEL_REQUIREMENTS.get(next_level)
            if not reqs:
                return None

            # Shartlarni tekshirish
            if total_xp >= reqs["xp"] and speaking_score >= reqs["speaking_score"]:
                return next_level
            return None

    def level_up(self, user_id: int, new_level: str) -> bool:
        """Darajani oshirish"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET current_level = ? WHERE user_id = ?",
                (new_level, user_id)
            )
            # Level up bonus XP
            self.add_xp(user_id, XP_REWARDS["level_up_bonus"], "level_up", f"{new_level} darajasiga o'tish")
            return cursor.rowcount > 0

    # ==================== MISTAKES ====================

    def add_mistake(self, user_id: int, user_input: str, correct_form: str,
                    mistake_type: str, grammar_rule: str = "",
                    mini_lesson: str = "", practice_exercises: str = "") -> int:
        """Xatoni saqlash"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mistakes (user_id, user_input, correct_form, mistake_type,
                                     grammar_rule, mini_lesson, practice_exercises, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, user_input, correct_form, mistake_type, grammar_rule,
                  mini_lesson, practice_exercises, datetime.datetime.now().isoformat()))
            return cursor.lastrowid

    def get_mistakes(self, user_id: int, mastered: bool = False, limit: int = 10) -> List[Dict]:
        """Foydalanuvchi xatolarini olish"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM mistakes
                WHERE user_id = ? AND is_mastered = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, 1 if mastered else 0, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_mistake_by_id(self, mistake_id: int) -> Optional[Dict]:
        """ID bo'yicha xatoni olish"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mistakes WHERE id = ?", (mistake_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def review_mistake(self, mistake_id: int) -> bool:
        """Xatoni ko'rib chiqish (review count +1)"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE mistakes
                SET reviewed_count = reviewed_count + 1,
                    last_reviewed = ?
                WHERE id = ?
            """, (datetime.datetime.now().isoformat(), mistake_id))
            return cursor.rowcount > 0

    def master_mistake(self, mistake_id: int) -> bool:
        """Xatoni o'zlashtirilgan deb belgilash"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE mistakes SET is_mastered = 1 WHERE id = ?",
                (mistake_id,)
            )
            return cursor.rowcount > 0

    def get_mistake_stats(self, user_id: int) -> Dict[str, int]:
        """Xatolar statistikasi"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as c FROM mistakes WHERE user_id = ? AND is_mastered = 0",
                (user_id,)
            )
            active = cursor.fetchone()["c"]
            cursor.execute(
                "SELECT COUNT(*) as c FROM mistakes WHERE user_id = ? AND is_mastered = 1",
                (user_id,)
            )
            mastered = cursor.fetchone()["c"]
            return {"active": active, "mastered": mastered, "total": active + mastered}

    # ==================== DAILY MISSIONS ====================

    def generate_daily_missions(self, user_id: int) -> List[Dict]:
        """Kunlik vazifalarni yaratish"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        with self._connect() as conn:
            cursor = conn.cursor()

            # Bugun allaqachon yaratilganmi?
            cursor.execute(
                "SELECT COUNT(*) as c FROM daily_missions WHERE user_id = ? AND date = ?",
                (user_id, today)
            )
            if cursor.fetchone()["c"] > 0:
                return self.get_today_missions(user_id)

            # User statistikasini olish
            stats = self.get_user_stats(user_id)
            level = stats.get("current_level", "a1")

            missions = []

            # 1. Flashcard vazifasi
            missions.append({
                "user_id": user_id,
                "date": today,
                "mission_type": "flashcard",
                "description": f"📚 {level.upper()} darajasidan 10 ta flashcard yodlang",
                "target_count": 10,
                "xp_reward": XP_REWARDS["flashcard_correct"] * 10,
            })

            # 2. AI suhbat vazifasi
            missions.append({
                "user_id": user_id,
                "date": today,
                "mission_type": "ai_conversation",
                "description": "🤖 AI Mentor bilan 1 ta suhbat o'tkazing",
                "target_count": 1,
                "xp_reward": XP_REWARDS["ai_conversation"],
            })

            # 3. Xatoni tuzatish (agar xatolar bo'lsa)
            if stats.get("active_mistakes", 0) > 0:
                missions.append({
                    "user_id": user_id,
                    "date": today,
                    "mission_type": "mistake_review",
                    "description": f"🔧 {stats['active_mistakes']} ta xatoni ko'rib chiqing",
                    "target_count": min(stats["active_mistakes"], 3),
                    "xp_reward": XP_REWARDS["mistake_corrected"] * 3,
                })

            # 4. Pomodoro vazifasi
            missions.append({
                "user_id": user_id,
                "date": today,
                "mission_type": "pomodoro",
                "description": "🍅 1 ta Pomodoro (25 daqiqa) o'tkazing",
                "target_count": 1,
                "xp_reward": XP_REWARDS["pomodoro_25min"],
            })

            # Vazifalarni saqlash
            for m in missions:
                cursor.execute("""
                    INSERT INTO daily_missions (user_id, date, mission_type, description, target_count, xp_reward)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (m["user_id"], m["date"], m["mission_type"], m["description"],
                      m["target_count"], m["xp_reward"]))

            return self.get_today_missions(user_id)

    def get_today_missions(self, user_id: int) -> List[Dict]:
        """Bugungi vazifalarni olish"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_missions
                WHERE user_id = ? AND date = ?
                ORDER BY id
            """, (user_id, today))
            return [dict(row) for row in cursor.fetchall()]

    def update_mission_progress(self, user_id: int, mission_type: str, increment: int = 1) -> Optional[Dict]:
        """Vazifa progressini yangilash"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_missions
                WHERE user_id = ? AND date = ? AND mission_type = ?
            """, (user_id, today, mission_type))
            mission = cursor.fetchone()
            if not mission:
                return None

            new_count = mission["current_count"] + increment
            is_completed = 1 if new_count >= mission["target_count"] else 0

            cursor.execute("""
                UPDATE daily_missions
                SET current_count = ?,
                    is_completed = ?,
                    completed_at = CASE WHEN ? >= target_count THEN ? ELSE completed_at END
                WHERE id = ?
            """, (new_count, is_completed, new_count,
                  datetime.datetime.now().isoformat() if is_completed else None,
                  mission["id"]))

            # Agar bajarilgan bo'lsa, XP berish
            if is_completed and not mission["is_completed"]:
                self.add_xp(user_id, mission["xp_reward"], "daily_mission", mission_type)

            return dict(cursor.execute("SELECT * FROM daily_missions WHERE id = ?", (mission["id"],)).fetchone())

    # ==================== SPEAKING SCORES ====================

    def add_speaking_score(self, user_id: int, session_type: str, topic: str,
                           score: float, feedback: str = "", words_used: str = "",
                           grammar_errors: str = "", duration_seconds: int = 0) -> int:
        """Speaking balini saqlash"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO speaking_scores (user_id, session_type, topic, score, feedback,
                                            words_used, grammar_errors, duration_seconds, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, session_type, topic, score, feedback, words_used,
                  grammar_errors, duration_seconds, datetime.datetime.now().isoformat()))

            # O'rtacha speaking score ni yangilash
            cursor.execute("""
                SELECT AVG(score) as avg_score FROM speaking_scores
                WHERE user_id = ?
            """, (user_id,))
            avg_score = cursor.fetchone()["avg_score"] or 0
            cursor.execute(
                "UPDATE users SET speaking_score = ? WHERE user_id = ?",
                (round(avg_score, 1), user_id)
            )

            return cursor.lastrowid

    def get_speaking_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Speaking tarixi"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM speaking_scores WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== LEKTION PROGRESS ====================

    def update_lektion_progress(self, user_id: int, level: str, book: str,
                                 lektion_number: int, flashcard_score: float = 0,
                                 words_learned: int = 0) -> bool:
        """Lektsiya progressini yangilash"""
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM lektion_progress
                WHERE user_id = ? AND level = ? AND book = ? AND lektion_number = ?
            """, (user_id, level, book, lektion_number))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE lektion_progress
                    SET flashcard_score = MAX(flashcard_score, ?),
                        words_learned = MAX(words_learned, ?)
                    WHERE id = ?
                """, (flashcard_score, words_learned, existing["id"]))
            else:
                cursor.execute("""
                    INSERT INTO lektion_progress (user_id, level, book, lektion_number, flashcard_score, words_learned)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, level, book, lektion_number, flashcard_score, words_learned))
            return True

    def complete_lektion(self, user_id: int, level: str, book: str, lektion_number: int) -> bool:
        """Lektsiyani bajarilgan deb belgilash"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE lektion_progress
                SET is_completed = 1, completed_at = ?
                WHERE user_id = ? AND level = ? AND book = ? AND lektion_number = ?
            """, (datetime.datetime.now().isoformat(), user_id, level, book, lektion_number))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO lektion_progress (user_id, level, book, lektion_number, is_completed, completed_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (user_id, level, book, lektion_number, datetime.datetime.now().isoformat()))
            return True

    def get_lektion_progress(self, user_id: int, level: str, book: str) -> List[Dict]:
        """Lektsiya progressi ro'yxati"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM lektion_progress
                WHERE user_id = ? AND level = ? AND book = ?
                ORDER BY lektion_number
            """, (user_id, level, book))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== VOICE PRACTICE ====================

    def add_voice_practice(self, user_id: int, german_word: str,
                           user_pronunciation: str = "", accuracy_score: float = 0,
                           feedback: str = "") -> int:
        """Ovozli mashqni saqlash"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO voice_practice (user_id, german_word, user_pronunciation, accuracy_score, feedback, practiced_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, german_word, user_pronunciation, accuracy_score, feedback,
                  datetime.datetime.now().isoformat()))
            return cursor.lastrowid

    def get_voice_practice_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Ovozli mashqlar tarixi"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM voice_practice WHERE user_id = ?
                ORDER BY practiced_at DESC LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== CONVERSATION HISTORY ====================

    def save_conversation(self, user_id: int, session_type: str, topic: str,
                          messages: List[Dict], words_learned_today: List[str] = None) -> int:
        """AI suhbatini saqlash"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_history (user_id, session_type, topic, messages, words_learned_today, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, session_type, topic, json.dumps(messages),
                  json.dumps(words_learned_today or []), datetime.datetime.now().isoformat()))

            # total_conversations ni yangilash
            cursor.execute(
                "UPDATE users SET total_conversations = total_conversations + 1 WHERE user_id = ?",
                (user_id,)
            )
            return cursor.lastrowid

    def get_recent_conversations(self, user_id: int, limit: int = 5) -> List[Dict]:
        """So'nggi suhbatlar"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversation_history WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["messages"] = json.loads(d["messages"])
                d["words_learned_today"] = json.loads(d["words_learned_today"]) if d["words_learned_today"] else []
                result.append(d)
            return result

    def get_words_learned_recent(self, user_id: int, days: int = 7) -> List[str]:
        """So'nggi N kunda o'rganilgan so'zlar"""
        with self._connect() as conn:
            cursor = conn.cursor()
            since = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT words_learned_today FROM conversation_history
                WHERE user_id = ? AND created_at > ?
            """, (user_id, since))
            all_words = []
            for row in cursor.fetchall():
                if row["words_learned_today"]:
                    all_words.extend(json.loads(row["words_learned_today"]))
            return list(set(all_words))


# Global database instance
_db: Database | None = None


def get_db() -> Database:
    """Global ma'lumotlar bazasi obyekti (singleton)"""
    global _db
    if _db is None:
        _db = Database()
    return _db
