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
    return json.loads(text)


def analyze_text(text: str, language: str = "uz") -> dict:
    """
    Matnni tahlil qilib min/o'rtacha/max savol sonini va (agar uzun bo'lsa)
    mavzular ro'yxatini qaytaradi.
    """
    system = (
        "Siz ta'lim kontenti tahlilchisisiz. Berilgan matn asosida undan qancha sifatli "
        "test savoli tuzish mumkinligini baholaysiz. FAQAT toza JSON qaytaring, boshqa "
        "hech qanday izoh yoki matn yozmang."
    )
    sample = text[:15000]
    user = f"""Til: {language}
Matn uzunligi: {len(text)} belgi

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

MATN:
\"\"\"{sample}\"\"\"
"""
    return _ask_json(system, user, max_tokens=1500)


def generate_quiz(text: str, language: str, question_count: int,
                   answer_format: str, scope_note: str = "") -> dict:
    """
    answer_format: 'AB', 'ABC' yoki 'ABCD'
    scope_note: masalan 'faqat 45-50 betlar' yoki 'faqat "Fotosintez" mavzusi'
    Qaytaradi: {"questions": [{"question": ..., "options": {...}, "correct": "A"}, ...]}
    """
    system = (
        "Siz tajribali test tuzuvchi metodistsiz. Berilgan matn asosida sifatli, aniq va "
        "matnga mos test savollari tuzasiz. FAQAT toza JSON qaytaring, boshqa hech qanday "
        "izoh yozmang."
    )
    n_options = len(answer_format)
    user = f"""Til: {language}
Kerakli savollar soni: {question_count}
Javob variantlari formati: {answer_format} ({n_options} ta variant)
Qamrov: {scope_note or "butun matn"}

Har bir savol uchun {n_options} ta variant bering, ulardan faqat bittasi to'g'ri bo'lsin.
Savollar matnga asoslangan, aniq, tushunarli va xilma-xil qiyinlikda bo'lsin.

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
