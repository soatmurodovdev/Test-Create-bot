<<<<<<< HEAD
# Murodjon Soatmurodov tomonidan yaratilgan
=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
"""
Google Gemini API bilan ishlash: matnni tahlil qilish va test generatsiya qilish.
Kutubxona: google-genai (rasmiy, tavsiya etilgan SDK)
"""
import json

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL

_client = None


def get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY sozlanmagan. https://aistudio.google.com dan bepul "
                "API kalit oling va config.py yoki GEMINI_API_KEY muhit "
                "o'zgaruvchisi orqali kiriting."
            )
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _ask_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> dict:
    client = get_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=0.4,
            response_mime_type="application/json",
        ),
    )
    text = (response.text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
<<<<<<< HEAD
    return json.loads(text)


def analyze_text(text: str, ui_language: str = "uz") -> dict:
    """
    Matnni tahlil qilib min/o'rtacha/max savol sonini va (agar uzun bo'lsa)
    mavzular ro'yxatini qaytaradi.

    MUHIM (V3): "topics" ro'yxati MATNNING O'ZI qaysi tilda yozilgan bo'lsa,
    o'sha tilda qaytariladi — bot interfeysi tilidan (ui_language) qat'i
    nazar. ui_language faqat AI'ga umumiy kontekst sifatida beriladi, matn
    tilini aniqlashda emas.
=======
    return json.loads(text, strict=False)


def analyze_text(text: str, language: str = "uz") -> dict:
    """
    Matnni tahlil qilib min/o'rtacha/max savol sonini va (agar uzun bo'lsa)
    mavzular ro'yxatini qaytaradi.
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
    """
    system = (
        "Siz ta'lim kontenti tahlilchisisiz. Berilgan matn asosida undan qancha sifatli "
        "test savoli tuzish mumkinligini baholaysiz. FAQAT toza JSON qaytaring, boshqa "
        "hech qanday izoh yoki matn yozmang."
    )
    sample = text[:15000]
<<<<<<< HEAD
    user = f"""Matn uzunligi: {len(text)} belgi
=======
    user = f"""Til: {language}
Matn uzunligi: {len(text)} belgi
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5

Quyidagi JSON formatda javob bering:
{{
  "min_questions": <int>,
  "avg_questions": <int>,
  "max_questions": <int>,
  "is_long": <true yoki false>,
  "topics": ["mavzu1", "mavzu2", ...]
}}

Qoidalar:
- "is_long" true bo'lsa, matn bir nechta aniq mavzuga bo'linadi va "topics" massivini to'ldiring.
- Matn qisqa/bir xil mavzu bo'lsa, "is_long": false va "topics": [] bo'lsin.
<<<<<<< HEAD
- MUHIM: "topics" ro'yxatidagi har bir mavzu nomini MATNNING O'ZI yozilgan
  tilida yozing (masalan matn ingliz tilida bo'lsa — mavzular ham ingliz
  tilida, matn rus tilida bo'lsa — ruscha). Buni matnni o'qib avtomatik
  aniqlang, boshqa tilga tarjima qilmang.
=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5

MATN:
\"\"\"{sample}\"\"\"
"""
    return _ask_json(system, user, max_tokens=1500)


_DIFFICULTY_HINTS = {
    "easy": "Savollar OSON darajada bo'lsin — asosiy tushunchalar, to'g'ridan-to'g'ri matndan topiladigan faktlar. Chalg'ituvchi variantlar aniq noto'g'ri bo'lsin.",
    "medium": "Savollar O'RTA darajada bo'lsin — tushunish va oddiy tahlil talab qiladigan, matn mazmunini bog'lay oladigan savollar.",
    "hard": "Savollar QIYIN darajada bo'lsin — chuqur tahlil, taqqoslash yoki xulosa chiqarishni talab qiladigan savollar. Chalg'ituvchi variantlar ishonchli va yaqin bo'lsin.",
}


<<<<<<< HEAD
def generate_quiz(text: str, question_count: int, answer_format: str,
                   scope_note: str = "", difficulty: str = "medium") -> dict:
=======
def generate_quiz(text: str, language: str, question_count: int,
                   answer_format: str, scope_note: str = "", difficulty: str = "medium") -> dict:
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
    """
    answer_format: 'AB', 'ABC' yoki 'ABCD'
    scope_note: masalan 'faqat 45-50 betlar' yoki 'faqat "Fotosintez" mavzusi'
    difficulty: 'easy', 'medium' yoki 'hard'
    Qaytaradi: {"questions": [{"question": ..., "options": {...}, "correct": "A"}, ...]}
<<<<<<< HEAD

    MUHIM (V3): savollar MATNNING O'ZI qaysi tilda yozilgan bo'lsa, o'sha
    tilda tuziladi — bot interfeysi tilidan qat'i nazar (masalan ingliz
    matn yuborilsa, interfeys o'zbekcha bo'lsa ham, test ingliz tilida
    chiqadi).
=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
    """
    system = (
        "Siz tajribali test tuzuvchi metodistsiz. Berilgan matn asosida sifatli, aniq va "
        "matnga mos test savollari tuzasiz. FAQAT toza JSON qaytaring, boshqa hech qanday "
        "izoh yozmang."
    )
    n_options = len(answer_format)
    difficulty_hint = _DIFFICULTY_HINTS.get(difficulty, _DIFFICULTY_HINTS["medium"])
<<<<<<< HEAD
    user = f"""Kerakli savollar soni: {question_count}
=======
    user = f"""MUHIM: Savollarni MATN qaysi tilda yozilgan bo'lsa, aynan SHU TILDA tuzing
(tilni matnning o'zidan avtomatik aniqlang). Foydalanuvchi interfeys tiliga ({language})
E'TIBOR BERMANG — faqat quyidagi MATN tiliga qarang.
Kerakli savollar soni: {question_count}
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
Javob variantlari formati: {answer_format} ({n_options} ta variant)
Qamrov: {scope_note or "butun matn"}
Qiyinlik darajasi: {difficulty_hint}

Har bir savol uchun {n_options} ta variant bering, ulardan faqat bittasi to'g'ri bo'lsin.
Savollar matnga asoslangan, aniq, tushunarli bo'lsin va yuqorida ko'rsatilgan qiyinlik
darajasiga izchil rioya qiling.

<<<<<<< HEAD
MUHIM — TIL: Savol va javob variantlarini MATNNING O'ZI qaysi tilda yozilgan
bo'lsa, aynan O'SHA TILDA tuzing. Tilni matnni o'qib avtomatik aniqlang,
boshqa tilga tarjima qilmang (masalan matn ingliz tilida bo'lsa, savollar
ham ingliz tilida bo'lsin).

=======
>>>>>>> 043a65b44659b22132508b88491bc6f3483f3db5
JSON format:
{{
  "questions": [
    {{
      "question": "...",
      "options": {{"A": "...", "B": "..."}},
      "correct": "A"
    }}
  ]
}}

MATN:
\"\"\"{text[:40000]}\"\"\"
"""
    return _ask_json(system, user, max_tokens=8000)
