<<<<<<< HEAD
# Test Tuzuvchi AI — AI Quiz Generator for Telegram

**Test Tuzuvchi AI** turns any document or block of text into a ready-to-use multiple-choice test in seconds. Send it a file or paste your text, and the bot's AI reads it, figures out how many good questions it can produce, and builds a complete quiz — questions and answers, in the format and language you need.

Try it: [@TestCreateAi_bot](https://t.me/TestCreateAi_bot)

---

## What the bot can do

### 📄 Accepts almost any source
Send the bot any of the following, or simply paste plain text:

- PDF
- Word (DOCX)
- Excel (XLSX / XLS)
- PowerPoint (PPTX)
- TXT, RTF, CSV
- EPUB (e-books)

### 🔍 Analyzes before generating
Before creating anything, the bot reads the full text and tells you:
- the **minimum**, **average**, and **maximum** number of quality questions it can realistically produce from that material
- if the text is long enough, it also detects and lists the distinct **topics** covered, so you can target one of them specifically

### 🎯 Full control over how the test is built
- **Scope** — build the test from the entire text, from one specific topic, or from a specific page range
- **Question count** — pick a suggested number or enter your own
- **Difficulty** — easy, medium, or hard
- **Answer format** — 2, 3, or 4 answer options per question (AB / ABC / ABCD)

### 🌐 Understands and responds in the right language
The bot's menus work in **Uzbek, Russian, or English** — whichever you choose. But the quiz itself is always generated in the **language of the source material you sent**, automatically detected, regardless of which interface language you're using. Send an English textbook chapter while using the Uzbek interface, and you get an English quiz.

### 📦 Delivers exactly what you need, in the format you want
Once generated, choose independently:
- **What to receive**: the questions, the answer key, or both
- **What format**: plain text in the chat, a nicely designed Word document, or a PDF — each branded and ready to print or share

### 🔄 Instant regeneration
Not happy with a result, or just want a fresh variant from the same material and settings? One tap regenerates a brand-new version of the test.

### 🛡️ Reliable by design
If something goes wrong on the AI side (a temporary service hiccup, for example), the bot never silently fails and never charges you for it — it offers a one-tap **Retry** instead.

---

## Getting your test — step by step

1. Open the bot and pick your interface language.
2. From the main menu, choose **Create test**.
3. Send a file or paste text.
4. Review the bot's estimate of possible question counts and topics.
5. Choose the scope, quantity, difficulty, and answer format.
6. The AI generates your quiz.
7. Pick what to receive (questions / answers / both) and in which format (text / Word / PDF).
8. Done — regenerate anytime, or start a new test.

---

## Plans and access

- **Free**: 2 tests per day, refreshed daily at no cost.
- **Subscriptions**: weekly, monthly, or yearly plans for unlimited testing, paid directly inside Telegram with **Telegram Stars** — no bank card or external payment needed.
- **Invite friends**: every friend who joins through your invite link earns you bonus tests.
- **Promo codes**: redeem a code for free access when one is shared with you.
- **My Account**: check your remaining free tests, bonus tests, and subscription status at any time from the main menu.

---

## Who it's for

- **Teachers** turning lesson material into ready-to-print exams
- **Students** self-testing on their own notes or textbooks
- **Tutoring centers** producing practice tests at scale
- Anyone who needs a quick, well-formatted quiz from any document, in any of three languages

---

Created by Murodjon Soatmurodov.
=======
# Test Tuzuvchi Bot

Foydalanuvchi yuborgan fayl yoki matn asosida Google Gemini AI yordamida test (savol-javob)
tuzib beruvchi Telegram bot.

## ⚠️ Xavfsizlik haqida MUHIM eslatma

Bot tokeningiz ushbu suhbatda ochiq ko'rinishda yuborilgan edi. Buni ko'rgan har
qanday kishi botingizni to'liq boshqarishi mumkin. Shu sababli:

1. Telegram’da **@BotFather** ga o'ting → `/mybots` → botingizni tanlang →
   **API Token** → **Revoke current token** — yangi token oling.
2. Yangi tokenni quyidagicha muhit o'zgaruvchisiga joylang (kodni tahrirlash shart emas):
   ```bash
   export BOT_TOKEN="YANGI_TOKENINGIZ"
   ```

Xuddi shunday, `GEMINI_API_KEY` ni ham hech qachon ochiq joyda ulashmang.

## Bepul Gemini API kalitini olish

1. **aistudio.google.com** ga o'ting va Google akkauntingiz bilan kiring
2. "Get API key" tugmasini bosing (kredit karta talab qilinmaydi)
3. Yangi loyiha yarating yoki mavjudini tanlang → kalit avtomatik yaratiladi
4. Kalitni nusxalab, quyidagicha muhit o'zgaruvchisiga joylang

## O'rnatish (Termux / Pydroid / oddiy server — barchasi bir xil)

```bash
pip install -r requirements.txt --break-system-packages   # Termux uchun kerak bo'lishi mumkin
export BOT_TOKEN="sizning_bot_tokeningiz"
export ADMIN_ID="5872019888"
export GEMINI_API_KEY="sizning_gemini_api_kalitingiz"
python main.py
```

Termux’da PDF/DOCX kutubxonalari ba'zan qo'shimcha paket talab qilishi mumkin
(`pkg install libxml2 libxslt` kabi) — xatolik chiqsa, xabarni o'qib mos paketni
o'rnating.

## Loyihaning tuzilishi

| Fayl              | Vazifasi                                                        |
|-------------------|-------------------------------------------------------------------|
| `main.py`         | Botni ishga tushiruvchi asosiy fayl                               |
| `config.py`       | Token, admin ID va boshqa sozlamalar                              |
| `database.py`     | SQLite: foydalanuvchilar va statistika                            |
| `file_parser.py`  | PDF/DOCX/XLSX/TXT/CSV/RTF/PPTX/EPUB dan matn ajratib olish        |
| `ai_service.py`   | Gemini API bilan matn tahlili va test generatsiyasi               |
| `export_docx.py`  | Tayyor testni Word (.docx) faylga aylantirish                     |
| `locales.py`      | O'zbek / Rus / Ingliz tillari uchun matnlar                        |
| `handlers.py`     | Botning barcha bosqichlari (holat mashinasi)                      |

## Foydalanuvchi oqimi

1. `/start` → til tanlash
2. Fayl yoki matn yuborish → AI matnni tahlil qiladi (min/o'rtacha/max savol soni,
   agar uzun bo'lsa — mavzular ro'yxati)
3. Qamrovni tanlash: to'liq matn / mavzu / sahifa oralig'i
4. Savollar sonini tanlash (tavsiya etilganlar yoki o'zi kiritadi)
5. Javob formati: AB / ABC / ABCD
6. AI test tuzadi
7. Natijani matn yoki `.docx` fayl ko'rinishida olish

## Admin panel

`/admin` buyrug'i faqat `ADMIN_ID` uchun ishlaydi:
- 📊 Statistika — jami foydalanuvchi, jami test, bugungi faollar, top foydalanuvchilar
- 👥 Foydalanuvchilar — umumiy son
- 📢 Xabar yuborish — barcha foydalanuvchilarga broadcast
- ⚙️ Sozlamalar — support va admin ma'lumotlari

## Keyingi qadamlar (ixtiyoriy yaxshilashlar)

- `context.user_data` hozircha faqat xotirada saqlanadi — bot qayta ishga tushsa,
  foydalanuvchi joriy bosqichini yo'qotadi. Kerak bo'lsa, `python-telegram-bot`
  ning `PicklePersistence`/`DictPersistence` mexanizmini qo'shish mumkin.
- `.doc` (eski Word format) qo'llab-quvvatlanmaydi — foydalanuvchidan `.docx`
  so'rash tavsiya etiladi, yoki `textract`/`antiword` orqali qo'shimcha qo'llab-
  quvvatlash qo'shish mumkin.
- Auto-clean funksiyasi uchun `handlers.schedule_delete()` tayyor — kerakli
  joylarda chaqirib, vaqtinchalik menyularni belgilangan vaqtdan so'ng
  o'chirishingiz mumkin.
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
