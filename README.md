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
