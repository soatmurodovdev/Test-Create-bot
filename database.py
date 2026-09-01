"""
Ma'lumotlar bazasi qatlami — Turso (libSQL) orqali.

MUHIM: Bu modul avvalgi sqlite3 asosidagi database.py o'rniga yozildi, LEKIN
jadval va ustun nomlari ATAYLAB bir xil qoldirildi (users.language,
users.tests_generated, users.joined_at/last_active, va h.k.) — shunday qilib
handlers.py va admin panel hech qanday o'zgarishsiz ishlayveradi.

Sabab: Render.com bepul tarifida disk VAQTINCHALIK (ephemeral) — bot
uxlab-uyg'onganda yoki qayta deploy qilinganda oddiy .db fayli butunlay
tozalanadi, shuning uchun statistika doim bo'sh chiqar edi.

Yechim: shu bir xil kod...
  - Termux'da (test uchun) LOKAL faylga ulanadi (TURSO_URL="file:testbot.db"
    — hech qanday internet yoki akkaunt kerak emas, oddiy SQLite kabi),
  - Render'da esa TURSO_URL/TURSO_AUTH_TOKEN orqali Turso bulutidagi doimiy
    bazaga ulanadi — ma'lumotlar hech qachon o'chmaydi.

`libsql-client` sof Python kutubxona (Rust/kompilyatsiya talab qilmaydi),
shuning uchun Termux'da muammosiz o'rnatiladi.
"""
import logging
import datetime

import libsql_client

from config import TURSO_URL, TURSO_AUTH_TOKEN

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        kwargs = {"url": TURSO_URL}
        if TURSO_AUTH_TOKEN:
            kwargs["auth_token"] = TURSO_AUTH_TOKEN
        _client = libsql_client.create_client_sync(**kwargs)
    return _client


def _now():
    return datetime.datetime.utcnow().isoformat()


def init_db():
    c = _get_client()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            language TEXT DEFAULT 'uz',
            joined_at TEXT,
            last_active TEXT,
            tests_generated INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS quiz_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question_count INTEGER,
            source_type TEXT,
            difficulty TEXT,
            created_at TEXT
        )
    """)
    logger.info("Baza tayyor: %s", TURSO_URL)


def upsert_user(user_id, username, full_name, language=None):
    c = _get_client()
    now = _now()
    rs = c.execute("SELECT user_id, language FROM users WHERE user_id = ?", [user_id])
    if rs.rows:
        current_lang = rs.rows[0][1]
        lang = language if language else current_lang
        c.execute(
            "UPDATE users SET username = ?, full_name = ?, language = ?, last_active = ? WHERE user_id = ?",
            [username or "", full_name or "", lang, now, user_id],
        )
    else:
        c.execute(
            "INSERT INTO users (user_id, username, full_name, language, joined_at, last_active) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [user_id, username or "", full_name or "", language or "uz", now, now],
        )


def set_language(user_id, language):
    c = _get_client()
    c.execute("UPDATE users SET language = ? WHERE user_id = ?", [language, user_id])


def get_language(user_id):
    c = _get_client()
    rs = c.execute("SELECT language FROM users WHERE user_id = ?", [user_id])
    if rs.rows:
        return rs.rows[0][0] or "uz"
    return "uz"


def log_quiz(user_id, question_count, source_type, difficulty=None):
    c = _get_client()
    now = _now()
    c.execute(
        "INSERT INTO quiz_log (user_id, question_count, source_type, difficulty, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        [user_id, question_count, source_type, difficulty or "", now],
    )
    c.execute(
        "UPDATE users SET tests_generated = tests_generated + 1 WHERE user_id = ?", [user_id]
    )


def get_stats():
    c = _get_client()
    total_users = c.execute("SELECT COUNT(*) FROM users").rows[0][0] or 0
    total_tests = c.execute("SELECT COUNT(*) FROM quiz_log").rows[0][0] or 0
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    active_today = c.execute(
        "SELECT COUNT(*) FROM users WHERE last_active LIKE ?", [f"{today}%"]
    ).rows[0][0] or 0
    top_rs = c.execute(
        "SELECT user_id, username, tests_generated FROM users "
        "ORDER BY tests_generated DESC LIMIT 5"
    )
    top_users = [
        {"user_id": r[0], "username": r[1], "tests_generated": r[2]} for r in top_rs.rows
    ]
    return {
        "total_users": total_users,
        "total_tests": total_tests,
        "active_today": active_today,
        "top_users": top_users,
    }


def all_user_ids():
    c = _get_client()
    rs = c.execute("SELECT user_id FROM users")
    return [row[0] for row in rs.rows]
