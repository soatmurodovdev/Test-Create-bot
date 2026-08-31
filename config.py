import os

# --- Telegram ---
# ESLATMA: Ushbu token suhbatda ochiq yuborilgan edi. Xavfsizlik uchun
# @BotFather -> /revoke orqali yangi token oling va uni shu yerga yoki
# .env faylga joylang.
BOT_TOKEN = os.getenv("BOT_TOKEN", "8988314813:AAE6DYzmaRef8hfRrWNwGvi8eX46oiq9IlU")

ADMIN_ID = int(os.getenv("ADMIN_ID", "5872019888"))
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@murodjon_soatmurodov")

# --- Google Gemini API (AI) ---
# Bepul API kalitni https://aistudio.google.com dan oling (karta shart emas)
# va shu yerga yoki muhit o'zgaruvchisiga joylang:
#   export GEMINI_API_KEY="AIza..."
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- Database ---
DB_PATH = os.getenv("DB_PATH", "testbot.db")

# --- Limits ---
MAX_FILE_SIZE_MB = 20
TEMP_MESSAGE_TTL = 60 * 10  # soniya - eskirgan xabarlarni avtomatik o'chirish uchun
