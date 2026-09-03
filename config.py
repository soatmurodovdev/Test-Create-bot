<<<<<<< HEAD
# Murodjon Soatmurodov tomonidan yaratilgan
=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
import os

# --- Telegram ---
# XAVFSIZLIK ESLATMA: repo GitHub'da PUBLIC (ochiq)! Tokenni hech qachon
# kodga yozib qo'ymang — faqat muhit o'zgaruvchisi (Termux: export, Render:
# Environment) orqali bering. Agar token oldin kodda ochiq turgan bo'lsa,
# @BotFather -> /revoke orqali darhol yangisini oling.
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@murodjon_soatmurodov")
<<<<<<< HEAD
# Referral havolalari uchun (masalan: t.me/TestCreateAi_bot?start=ref_123)
BOT_USERNAME = os.getenv("BOT_USERNAME", "TestCreateAi_bot")
=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5

# --- Google Gemini API (AI) ---
# Bepul API kalitni https://aistudio.google.com dan oling (karta shart emas)
# va muhit o'zgaruvchisiga joylang: export GEMINI_API_KEY="..."
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# --- Database (Turso / libSQL) ---
# Termux'da (test uchun) hech narsa sozlamasangiz ham ishlaydi — lokal
# "testbot.db" fayliga yozadi. Render'ga deploy qilganda TURSO_URL va
# TURSO_AUTH_TOKEN'ni muhit o'zgaruvchisi sifatida bering (Turso bulut bazasi
# — ma'lumotlar hech qachon o'chmaydi, Render disk tozalansa ham).
TURSO_URL = os.getenv("TURSO_URL", "file:testbot.db")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

# --- Limits ---
MAX_FILE_SIZE_MB = 20
TEMP_MESSAGE_TTL = 60 * 10  # soniya - eskirgan xabarlarni avtomatik o'chirish uchun

# --- V2: qiyinlik darajalari ---
DIFFICULTIES = ("easy", "medium", "hard")
