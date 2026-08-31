import sqlite3
import threading
from datetime import datetime

from config import DB_PATH

_lock = threading.Lock()


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                language TEXT DEFAULT 'uz',
                joined_at TEXT,
                last_active TEXT,
                tests_generated INTEGER DEFAULT 0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_count INTEGER,
                source_type TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
        conn.close()


def upsert_user(user_id, username, full_name, language=None):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute("SELECT user_id, language FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if row:
            lang = language if language else row["language"]
            cur.execute(
                "UPDATE users SET username=?, full_name=?, language=?, last_active=? WHERE user_id=?",
                (username, full_name, lang, now, user_id),
            )
        else:
            cur.execute(
                "INSERT INTO users (user_id, username, full_name, language, joined_at, last_active) "
                "VALUES (?,?,?,?,?,?)",
                (user_id, username, full_name, language or "uz", now, now),
            )
        conn.commit()
        conn.close()


def set_language(user_id, language):
    with _lock:
        conn = get_conn()
        conn.execute("UPDATE users SET language=? WHERE user_id=?", (language, user_id))
        conn.commit()
        conn.close()


def get_language(user_id):
    with _lock:
        conn = get_conn()
        row = conn.execute("SELECT language FROM users WHERE user_id=?", (user_id,)).fetchone()
        conn.close()
        return row["language"] if row else "uz"


def log_quiz(user_id, question_count, source_type):
    with _lock:
        conn = get_conn()
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO quiz_log (user_id, question_count, source_type, created_at) VALUES (?,?,?,?)",
            (user_id, question_count, source_type, now),
        )
        conn.execute(
            "UPDATE users SET tests_generated = tests_generated + 1 WHERE user_id=?", (user_id,)
        )
        conn.commit()
        conn.close()


def get_stats():
    with _lock:
        conn = get_conn()
        total_users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        total_tests = conn.execute("SELECT COUNT(*) c FROM quiz_log").fetchone()["c"]
        today = datetime.utcnow().strftime("%Y-%m-%d")
        active_today = conn.execute(
            "SELECT COUNT(*) c FROM users WHERE last_active LIKE ?", (today + "%",)
        ).fetchone()["c"]
        top_users = conn.execute(
            "SELECT user_id, username, tests_generated FROM users ORDER BY tests_generated DESC LIMIT 5"
        ).fetchall()
        conn.close()
        return {
            "total_users": total_users,
            "total_tests": total_tests,
            "active_today": active_today,
            "top_users": [dict(r) for r in top_users],
        }


def all_user_ids():
    with _lock:
        conn = get_conn()
        rows = conn.execute("SELECT user_id FROM users").fetchall()
        conn.close()
        return [r["user_id"] for r in rows]
