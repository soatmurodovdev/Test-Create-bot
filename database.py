<<<<<<< HEAD
# Murodjon Soatmurodov tomonidan yaratilgan
"""
Ma'lumotlar bazasi qatlami — Turso (libSQL) orqali.

V3: monetizatsiya (kunlik bepul limit, Stars obunalar, referral bonus,
promokod) uchun kerakli jadval/ustunlar qo'shildi. Bot ALLAQACHON ishlab
turgan production bazaga ega bo'lgani uchun (V2), yangi ustunlar oddiy
CREATE TABLE bilan emas, xavfsiz "ustun bormi-yo'qmi" tekshiruvi orqali
(ALTER TABLE ... ADD COLUMN) qo'shiladi — shunday qilib eski
foydalanuvchilar ma'lumoti YO'QOLMAYDI.
=======
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
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
"""
import logging
import datetime

import libsql_client

from config import TURSO_URL, TURSO_AUTH_TOKEN

logger = logging.getLogger(__name__)

_client = None

<<<<<<< HEAD
DAILY_FREE_LIMIT = 2
BONUS_PER_REFERRAL = 2
BONUS_VALID_DAYS = 7

PLAN_DAYS = {"weekly": 7, "monthly": 30, "yearly": 365}
PLAN_STARS = {"weekly": 50, "monthly": 150, "yearly": 1750}

=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5

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


<<<<<<< HEAD
def _today():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def _column_exists(c, table, column):
    rs = c.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in rs.rows)


def _ensure_column(c, table, column, ddl):
    if not _column_exists(c, table, column):
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        logger.info("Baza migratsiyasi: %s.%s qo'shildi", table, column)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
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
<<<<<<< HEAD

    # --- V3 uchun xavfsiz migratsiya (mavjud jadvalni buzmaydi) ---
    _ensure_column(c, "users", "subscription_plan", "TEXT DEFAULT 'none'")
    _ensure_column(c, "users", "subscription_until", "TEXT")
    _ensure_column(c, "users", "daily_free_used", "INTEGER DEFAULT 0")
    _ensure_column(c, "users", "daily_reset_date", "TEXT")
    _ensure_column(c, "users", "bonus_tests", "INTEGER DEFAULT 0")
    _ensure_column(c, "users", "bonus_expires", "TEXT")
    _ensure_column(c, "users", "referred_by", "INTEGER")
    _ensure_column(c, "users", "referral_count", "INTEGER DEFAULT 0")

    c.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            plan TEXT NOT NULL,
            max_uses INTEGER NOT NULL,
            used_count INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at TEXT,
            expires_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS promo_redemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            user_id INTEGER,
            redeemed_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            stars_amount INTEGER,
            plan TEXT,
            created_at TEXT
        )
    """)
    logger.info("Baza tayyor: %s", TURSO_URL)


# ---------------------------------------------------------------------------
# Users (V2'dan o'zgarishsiz)
# ---------------------------------------------------------------------------

=======
    logger.info("Baza tayyor: %s", TURSO_URL)


>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
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
<<<<<<< HEAD
    """Faqat statistik yozuv (admin panel uchun) — kvotaga tegmaydi."""
=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
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
<<<<<<< HEAD
    today = _today()
=======
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
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
<<<<<<< HEAD
    total_stars = c.execute(
        "SELECT COALESCE(SUM(stars_amount), 0) FROM payments"
    ).rows[0][0] or 0
=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
    return {
        "total_users": total_users,
        "total_tests": total_tests,
        "active_today": active_today,
        "top_users": top_users,
<<<<<<< HEAD
        "total_stars": total_stars,
=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
    }


def all_user_ids():
    c = _get_client()
    rs = c.execute("SELECT user_id FROM users")
    return [row[0] for row in rs.rows]
<<<<<<< HEAD


# ---------------------------------------------------------------------------
# V3: Kvota (bepul limit / obuna / bonus)
# ---------------------------------------------------------------------------

def _row_to_access(row):
    (sub_plan, sub_until, daily_used, daily_reset, bonus, bonus_exp) = row
    return {
        "subscription_plan": sub_plan or "none",
        "subscription_until": sub_until,
        "daily_free_used": daily_used or 0,
        "daily_reset_date": daily_reset,
        "bonus_tests": bonus or 0,
        "bonus_expires": bonus_exp,
    }


def _get_access_row(c, user_id):
    rs = c.execute(
        "SELECT subscription_plan, subscription_until, daily_free_used, "
        "daily_reset_date, bonus_tests, bonus_expires FROM users WHERE user_id = ?",
        [user_id],
    )
    if not rs.rows:
        return None
    return _row_to_access(rs.rows[0])


def _reset_daily_if_needed(c, user_id, access):
    today = _today()
    if access["daily_reset_date"] != today:
        c.execute(
            "UPDATE users SET daily_free_used = 0, daily_reset_date = ? WHERE user_id = ?",
            [today, user_id],
        )
        access["daily_free_used"] = 0
        access["daily_reset_date"] = today
    return access


def _subscription_active(access):
    until = access.get("subscription_until")
    if not until:
        return False
    try:
        return datetime.datetime.fromisoformat(until) > datetime.datetime.utcnow()
    except ValueError:
        return False


def _bonus_available(access):
    if access.get("bonus_tests", 0) <= 0:
        return 0
    expires = access.get("bonus_expires")
    if not expires:
        return 0
    try:
        if datetime.datetime.fromisoformat(expires) <= datetime.datetime.utcnow():
            return 0
    except ValueError:
        return 0
    return access["bonus_tests"]


def can_generate_test(user_id):
    """
    Qaytaradi: (ruxsat_bormi: bool, sabab: str)
    sabab: "subscription" | "daily" | "bonus" | "none"
    """
    c = _get_client()
    access = _get_access_row(c, user_id)
    if access is None:
        return False, "none"
    access = _reset_daily_if_needed(c, user_id, access)

    if _subscription_active(access):
        return True, "subscription"
    if access["daily_free_used"] < DAILY_FREE_LIMIT:
        return True, "daily"
    if _bonus_available(access) > 0:
        return True, "bonus"
    return False, "none"


def consume_quota(user_id):
    """Test MUVAFFAQIYATLI tuzilgandan KEYIN chaqiriladi. Texnik xato bo'lsa
    bu funksiya umuman chaqirilmaydi — shu bilan xato holatlar kvotani
    yemaydi."""
    c = _get_client()
    access = _get_access_row(c, user_id)
    if access is None:
        return
    access = _reset_daily_if_needed(c, user_id, access)

    if _subscription_active(access):
        return  # obuna faol — cheksiz, kvota kamaymaydi
    if access["daily_free_used"] < DAILY_FREE_LIMIT:
        c.execute(
            "UPDATE users SET daily_free_used = daily_free_used + 1 WHERE user_id = ?",
            [user_id],
        )
        return
    if _bonus_available(access) > 0:
        c.execute(
            "UPDATE users SET bonus_tests = bonus_tests - 1 WHERE user_id = ?", [user_id]
        )
        return


def get_access_summary(user_id):
    """Foydalanuvchiga holatini ko'rsatish uchun (paywall xabarlarida)."""
    c = _get_client()
    access = _get_access_row(c, user_id)
    if access is None:
        return None
    access = _reset_daily_if_needed(c, user_id, access)
    access["subscription_active"] = _subscription_active(access)
    access["bonus_available"] = _bonus_available(access)
    access["daily_remaining"] = max(0, DAILY_FREE_LIMIT - access["daily_free_used"])
    return access


def get_referral_count(user_id):
    c = _get_client()
    rs = c.execute("SELECT referral_count FROM users WHERE user_id = ?", [user_id])
    if rs.rows:
        return rs.rows[0][0] or 0
    return 0


# ---------------------------------------------------------------------------
# V3: Obuna berish (Stars to'lovi yoki promokod orqali)
# ---------------------------------------------------------------------------

def grant_subscription(user_id, plan):
    """plan: 'weekly' | 'monthly' | 'yearly'. Joriy obuna muddati bo'lsa,
    ustiga qo'shiladi (stacking)."""
    days = PLAN_DAYS.get(plan)
    if not days:
        raise ValueError(f"Noma'lum reja: {plan}")

    c = _get_client()
    rs = c.execute("SELECT subscription_until FROM users WHERE user_id = ?", [user_id])
    current_until = rs.rows[0][0] if rs.rows else None

    now = datetime.datetime.utcnow()
    base = now
    if current_until:
        try:
            existing = datetime.datetime.fromisoformat(current_until)
            if existing > now:
                base = existing
        except ValueError:
            pass

    new_until = (base + datetime.timedelta(days=days)).isoformat()
    c.execute(
        "UPDATE users SET subscription_plan = ?, subscription_until = ? WHERE user_id = ?",
        [plan, new_until, user_id],
    )
    return new_until


def log_payment(user_id, stars_amount, plan):
    c = _get_client()
    c.execute(
        "INSERT INTO payments (user_id, stars_amount, plan, created_at) VALUES (?, ?, ?, ?)",
        [user_id, stars_amount, plan, _now()],
    )


# ---------------------------------------------------------------------------
# V3: Referral
# ---------------------------------------------------------------------------

def register_referral(new_user_id, referrer_id):
    """Yangi foydalanuvchi referral havola orqali kirganda chaqiriladi.
    Qaytaradi: True agar bonus berilgan bo'lsa, False agar yo'q (masalan
    o'zini-o'zi taklif qilgan yoki avval allaqachon referral qilingan)."""
    if new_user_id == referrer_id:
        return False

    c = _get_client()
    rs = c.execute("SELECT referred_by FROM users WHERE user_id = ?", [new_user_id])
    if not rs.rows:
        return False
    if rs.rows[0][0]:
        return False  # allaqachon kimdir orqali kelgan

    referrer_rs = c.execute("SELECT user_id FROM users WHERE user_id = ?", [referrer_id])
    if not referrer_rs.rows:
        return False  # referrer bazada yo'q (hech qachon /start bosmagan)

    c.execute(
        "UPDATE users SET referred_by = ? WHERE user_id = ?", [referrer_id, new_user_id]
    )

    new_bonus_expires = (datetime.datetime.utcnow() + datetime.timedelta(days=BONUS_VALID_DAYS)).isoformat()
    c.execute(
        "UPDATE users SET bonus_tests = bonus_tests + ?, bonus_expires = ?, "
        "referral_count = referral_count + 1 WHERE user_id = ?",
        [BONUS_PER_REFERRAL, new_bonus_expires, referrer_id],
    )
    return True


# ---------------------------------------------------------------------------
# V3: Promokod (faqat admin yaratadi)
# ---------------------------------------------------------------------------

def create_promo_code(code, plan, max_uses, created_by, expires_at=None):
    if plan not in PLAN_DAYS:
        raise ValueError(f"Noma'lum reja: {plan}")
    c = _get_client()
    c.execute(
        "INSERT INTO promo_codes (code, plan, max_uses, used_count, created_by, created_at, expires_at) "
        "VALUES (?, ?, ?, 0, ?, ?, ?)",
        [code, plan, max_uses, created_by, _now(), expires_at],
    )


def redeem_promo_code(code, user_id):
    """Qaytaradi: (success: bool, reason: str, plan: str|None)
    reason: 'ok' | 'not_found' | 'expired' | 'exhausted' | 'already_used'"""
    c = _get_client()
    rs = c.execute(
        "SELECT plan, max_uses, used_count, expires_at FROM promo_codes WHERE code = ?", [code]
    )
    if not rs.rows:
        return False, "not_found", None

    plan, max_uses, used_count, expires_at = rs.rows[0]

    if expires_at:
        try:
            if datetime.datetime.fromisoformat(expires_at) <= datetime.datetime.utcnow():
                return False, "expired", None
        except ValueError:
            pass

    if used_count >= max_uses:
        return False, "exhausted", None

    already = c.execute(
        "SELECT id FROM promo_redemptions WHERE code = ? AND user_id = ?", [code, user_id]
    )
    if already.rows:
        return False, "already_used", None

    grant_subscription(user_id, plan)
    c.execute("UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?", [code])
    c.execute(
        "INSERT INTO promo_redemptions (code, user_id, redeemed_at) VALUES (?, ?, ?)",
        [code, user_id, _now()],
    )
    return True, "ok", plan
=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
