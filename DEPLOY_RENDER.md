# Botni Render.com'ga joylashtirish (bepul, karta kerak emas)

Bu yo'riqnoma botni Termux'dan Render'ga ko'chirib, uni **UptimeRobot** yordamida
doim ishlab turadigan qilib qo'yish uchun.

---

## 1-QADAM: Kodni GitHub'ga yuklash

Render GitHub repo orqali ishlaydi, shuning uchun avval kodni GitHub'ga qo'yish kerak.

Termux'da (loyiha papkasida):

```bash
pkg install git -y
cd ~/quiz_bot   # loyihangiz papkasi nomi
git init
git add .
git commit -m "Birinchi versiya"
```

GitHub'da yangi **bo'sh** (README'siz) repository yarating (masalan `quiz-bot`),
so'ng:

```bash
git branch -M main
git remote add origin https://github.com/FOYDALANUVCHI_NOMI/quiz-bot.git
git push -u origin main
```

⚠️ **MUHIM:** `config.py` faylida token va API kalitlar hozircha ochiq turibdi.
GitHub'ga yuklashdan oldin, `config.py`dagi haqiqiy qiymatlarni olib tashlab,
faqat `os.getenv(...)` orqali o'qiladigan qilib qoldiring (kod allaqachon shunday
yozilgan — `os.getenv("BOT_TOKEN", "AAAA...")` ko'rinishida). Xavfsizroq bo'lishi
uchun ikkinchi argumentni (standart qiymatni) ham o'chirib tashlang, token va
kalitlarni Render sozlamalarida (pastda ko'rsatiladi) kiritasiz.

---

## 2-QADAM: Render'da hisob ochish va deploy qilish

1. https://render.com ga kiring, **"Get Started"** — GitHub hisobingiz orqali
   ro'yxatdan o'ting (karta so'ralmaydi).
2. Dashboard'da **"New +"** → **"Web Service"** ni tanlang.
3. GitHub repongizni (`quiz-bot`) tanlang va ulang.
4. Sozlamalar avtomatik `render.yaml` fayldan olinadi. Agar qo'lda kiritish
   so'ralsa:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** Free
5. **Environment Variables** (Muhit o'zgaruvchilari) bo'limida quyidagilarni
   qo'shing:
   - `USE_WEBHOOK` = `1`
   - `BOT_TOKEN` = (sizning bot tokeningiz)
   - `ADMIN_ID` = (sizning Telegram ID'ingiz)
   - `GEMINI_API_KEY` = (sizning Gemini API kalitingiz)
   - `SUPPORT_USERNAME` = `@murodjon_soatmurodov`
6. **"Create Web Service"** tugmasini bosing.

Render kodni yuklab, o'rnatib, ishga tushiradi (bir necha daqiqa vaqt oladi).
Loglar (Logs) bo'limida `Bot WEBHOOK rejimida ishga tushdi...` degan yozuvni
ko'rsangiz — bot ishlayapti.

Sizning bot manzilingiz: `https://quiz-bot-XXXX.onrender.com` (Render o'zi
beradi, buni "Settings" bo'limida ko'rasiz).

---

## 3-QADAM: UptimeRobot bilan doim uyg'oq ushlab turish

Render'ning bepul tarifi 15 daqiqa faoliyatsizlikdan keyin dasturni "uxlatib
qo'yadi". Buning oldini olish uchun UptimeRobot orqali har 5 daqiqada botning
manziliga so'rov yuboramiz.

1. https://uptimerobot.com ga kiring, bepul ro'yxatdan o'ting (karta kerak
   emas).
2. **"+ Add New Monitor"** tugmasini bosing.
3. Sozlamalar:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Quiz Bot
   - **URL:** `https://quiz-bot-XXXX.onrender.com` (Render bergan manzil,
     oxiriga `/` qo'yish shart emas)
   - **Monitoring Interval:** 5 minutes (eng kichik bepul interval)
4. **"Create Monitor"** ni bosing.

Shu bilan tamom — UptimeRobot endi har 5 daqiqada botingizga "salom" aytib
turadi, va bot hech qachon uxlab qolmaydi. Bot bu so'rovlarga 404 xato bilan
javob berishi mumkin (chunki UptimeRobot webhook manziliga emas, asosiy
manzilga so'rov yuboradi) — bu **muammo emas**, chunki Render uchun muhimi
so'rov kelishi, javobning mazmuni emas.

---

## 4-QADAM: Tekshirish

Telegram'da botingizga `/start` yuboring — javob kelishi kerak. Agar birinchi
xabar biroz sekinroq kelsa (bot hali "uyg'onayotgan" bo'lishi mumkin), bu
normal — keyingi xabarlar tezroq keladi.

---

## Kelajakda kod yangilansa

Kodga o'zgartirish kiritsangiz, shunchaki:

```bash
git add .
git commit -m "Yangilanish tavsifi"
git push
```

Render buni avtomatik aniqlab, botni qayta deploy qiladi (agar "Auto-Deploy"
yoqilgan bo'lsa — bu odatiy holat).

---

## Eslatmalar

- `testbot.db` fayli — bu sizning Termux'dagi ma'lumotlar bazangiz. Render'da
  bot birinchi marta ishga tushganda **yangi, bo'sh** baza yaratiladi (chunki
  Render'ning bepul tarifida disk vaqtinchalik — har safar qayta ishga
  tushganda fayllar tozalanishi mumkin). Agar foydalanuvchilar tarixini
  saqlab qolish kerak bo'lsa, buni keyinroq tashqi bazaga (masalan Render'ning
  bepul PostgreSQL'iga) ko'chirish tavsiya etiladi — hozircha MVP uchun bu
  muammo emas.
- Bot tokeningiz va API kalitlaringizni hech qachon ochiq (public) repo
  tavsifiga yoki kodga yozmang — faqat Render Environment Variables orqali
  bering.
