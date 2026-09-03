# Murodjon Soatmurodov tomonidan yaratilgan
import os
import asyncio
import logging
import tempfile
import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes

import database
import file_parser
import ai_service
import branded_output
from locales import T
from config import ADMIN_ID, SUPPORT_USERNAME, BOT_USERNAME, MAX_FILE_SIZE_MB, TEMP_MESSAGE_TTL

logger = logging.getLogger(__name__)

SUPPORTED_EXTS = {"pdf", "docx", "xlsx", "xls", "txt", "rtf", "csv", "pptx", "epub"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def lang_of(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str:
    return context.user_data.get("language") or database.get_language(user_id)


def tr(context: ContextTypes.DEFAULT_TYPE, user_id: int, key: str, **kwargs) -> str:
    lang = lang_of(context, user_id)
    text = T.get(lang, T["uz"]).get(key, key)
    return text.format(**kwargs) if kwargs else text


def tr_lang(lang: str, key: str, **kwargs) -> str:
    """tr() ning versiyasi — boshqa foydalanuvchiga (masalan referrerga)
    xabar yozganda, uning tilini to'g'ridan-to'g'ri berish uchun."""
    text = T.get(lang, T["uz"]).get(key, key)
    return text.format(**kwargs) if kwargs else text


async def _delete_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    try:
        await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
    except Exception:
        pass


def schedule_delete(context: ContextTypes.DEFAULT_TYPE, chat_id, message_id, delay=TEMP_MESSAGE_TTL):
    if context.job_queue:
        context.job_queue.run_once(_delete_job, when=delay, data={"chat_id": chat_id, "message_id": message_id})


# ---------------------------------------------------------------------------
# /start, referral payload, language selection
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    database.upsert_user(user.id, user.username, user.full_name)
    context.user_data.clear()

    # --- Referral havolasi orqali kirgan bo'lsa (t.me/bot?start=ref_123) ---
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0][4:])
        except ValueError:
            referrer_id = None
        if referrer_id:
            granted = database.register_referral(new_user_id=user.id, referrer_id=referrer_id)
            if granted:
                try:
                    referrer_lang = database.get_language(referrer_id)
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=tr_lang(referrer_lang, "referral_bonus_notice"),
                    )
                except Exception:
                    logger.warning("Referrer %s ga xabar yuborilmadi", referrer_id)

    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang:uz"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
            ]
        ]
    )
    await update.message.reply_text(
        "Tilni tanlang / Выберите язык / Choose language:", reply_markup=kb
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data.clear()
    await update.message.reply_text(tr(context, user_id, "cancelled"))


# ---------------------------------------------------------------------------
# Asosiy menyu
# ---------------------------------------------------------------------------

def _main_menu_buttons(context, user_id):
    return [
        [InlineKeyboardButton(tr(context, user_id, "menu_test"), callback_data="menu:test")],
        [InlineKeyboardButton(tr(context, user_id, "menu_subscribe"), callback_data="menu:subscribe")],
        [InlineKeyboardButton(tr(context, user_id, "menu_promo"), callback_data="menu:promo")],
        [InlineKeyboardButton(tr(context, user_id, "menu_referral"), callback_data="menu:referral")],
        [InlineKeyboardButton(tr(context, user_id, "menu_account"), callback_data="menu:account")],
        [InlineKeyboardButton(tr(context, user_id, "menu_language"), callback_data="menu:language")],
    ]


async def show_main_menu(query, context, user_id):
    context.user_data.pop("awaiting_promo_redeem", None)
    context.user_data.pop("awaiting_custom_qty", None)
    context.user_data.pop("awaiting_page_range", None)
    await query.edit_message_text(
        tr(context, user_id, "main_menu_title"),
        reply_markup=InlineKeyboardMarkup(_main_menu_buttons(context, user_id)),
    )


async def show_main_menu_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    await update.message.reply_text(
        tr(context, user_id, "main_menu_title"),
        reply_markup=InlineKeyboardMarkup(_main_menu_buttons(context, user_id)),
    )


# ---------------------------------------------------------------------------
# Callback router
# ---------------------------------------------------------------------------

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("lang:"):
        await handle_lang(update, context, data.split(":", 1)[1])
    elif data == "menu":
        await show_main_menu(query, context, user_id)
    elif data.startswith("menu:"):
        await handle_menu(update, context, data.split(":", 1)[1])
    elif data.startswith("scope:"):
        await handle_scope(update, context, data.split(":", 1)[1])
    elif data.startswith("topicpick:"):
        idx = int(data.split(":", 1)[1])
        topics = context.user_data.get("topics_list", [])
        context.user_data["scope_detail"] = topics[idx] if idx < len(topics) else ""
        await ask_quantity_edit(query, context, user_id)
    elif data.startswith("qty:"):
        await handle_qty(update, context, data.split(":", 1)[1])
    elif data.startswith("diff:"):
        await handle_difficulty(update, context, data.split(":", 1)[1])
    elif data.startswith("fmt:"):
        await handle_fmt(update, context, data.split(":", 1)[1])
    elif data.startswith("content:"):
        await handle_content(update, context, data.split(":", 1)[1])
    elif data.startswith("out:"):
        _, content, fmt = data.split(":", 2)
        await handle_output(update, context, content, fmt)
    elif data == "regen":
        await handle_regenerate(update, context)
    elif data == "retry_gen":
        await handle_retry_generation(update, context)
    elif data == "back_to_content":
        questions = context.user_data.get("quiz_result", [])
        if questions:
            await show_content_choice(query, context, user_id, len(questions))
        else:
            await query.edit_message_text(tr(context, user_id, "nothing_to_export"))
    elif data == "back":
        await handle_back(update, context)
    elif data.startswith("buy:"):
        await handle_buy(update, context, data.split(":", 1)[1])
    elif data.startswith("admin:"):
        await handle_admin_callback(update, context, data.split(":", 1)[1])


async def handle_lang(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    user_id = update.effective_user.id
    context.user_data["language"] = lang
    database.set_language(user_id, lang)
    query = update.callback_query
    await show_main_menu(query, context, user_id)


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, item: str):
    query = update.callback_query
    user_id = query.from_user.id

    if item == "test":
        await query.edit_message_text(
            tr(context, user_id, "welcome"),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(tr(context, user_id, "menu_btn"), callback_data="menu")]]
            ),
        )
    elif item == "subscribe":
        await show_subscribe_menu(query, context, user_id)
    elif item == "promo":
        context.user_data["awaiting_promo_redeem"] = True
        await query.edit_message_text(
            tr(context, user_id, "promo_ask_code"),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(tr(context, user_id, "menu_btn"), callback_data="menu")]]
            ),
        )
    elif item == "referral":
        await show_referral_info(query, context, user_id)
    elif item == "account":
        await show_account_info(query, context, user_id)
    elif item == "language":
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang:uz"),
                    InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
                    InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
                ]
            ]
        )
        await query.edit_message_text(
            "Tilni tanlang / Выберите язык / Choose language:", reply_markup=kb
        )


# ---------------------------------------------------------------------------
# Receiving a document or plain text
# ---------------------------------------------------------------------------

async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document

    if doc.file_size and doc.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        await update.message.reply_text(tr(context, user_id, "file_too_big", mb=MAX_FILE_SIZE_MB))
        return

    ext = os.path.splitext(doc.file_name or "")[1].lstrip(".").lower()
    if ext not in SUPPORTED_EXTS:
        await update.message.reply_text(tr(context, user_id, "unsupported_format", ext=ext))
        return

    status_msg = await update.message.reply_text(tr(context, user_id, "processing_file"))

    tg_file = await doc.get_file()
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp_path = tmp.name
    await tg_file.download_to_drive(tmp_path)

    try:
        # Katta fayllarni o'qish sekin bo'lishi mumkin — bu botning boshqa
        # so'rovlarga javob berishini to'sib qo'ymasligi uchun alohida
        # oqimda (thread) bajaramiz.
        text = await asyncio.to_thread(file_parser.extract_text, tmp_path, ext)
    except Exception as e:
        logger.exception("File parse error")
        await status_msg.edit_text(tr(context, user_id, "parse_error", error=str(e)))
        return
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if not text or len(text.strip()) < 50:
        await status_msg.edit_text(tr(context, user_id, "empty_text"))
        return

    context.user_data["raw_text"] = text
    context.user_data["source_type"] = ext
    await status_msg.edit_text(tr(context, user_id, "analyzing"))
    await run_analysis(update, context, status_msg)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Admin: xabar tarqatish (broadcast)
    if context.user_data.get("awaiting_broadcast") and user_id == ADMIN_ID:
        await do_broadcast(update, context)
        return

    # Admin: promokod yaratish
    if context.user_data.get("awaiting_admin_promo") and user_id == ADMIN_ID:
        await do_create_promo(update, context)
        return

    # Foydalanuvchi: promokod kiritish
    if context.user_data.get("awaiting_promo_redeem"):
        context.user_data["awaiting_promo_redeem"] = False
        await do_redeem_promo(update, context)
        return

    # Custom question count flow
    if context.user_data.get("awaiting_custom_qty"):
        txt = update.message.text.strip()
        if txt.isdigit() and int(txt) > 0:
            context.user_data["awaiting_custom_qty"] = False
            await set_quantity_and_ask_difficulty(update, context, int(txt))
        else:
            await update.message.reply_text(tr(context, user_id, "invalid_number"))
        return

    # Custom page range flow
    if context.user_data.get("awaiting_page_range"):
        context.user_data["awaiting_page_range"] = False
        context.user_data["scope_detail"] = f"faqat {update.message.text.strip()} sahifalar"
        await ask_quantity(update, context)
        return

    text = update.message.text
    if not text or len(text.strip()) < 50:
        await update.message.reply_text(tr(context, user_id, "send_file_or_text"))
        return

    context.user_data["raw_text"] = text
    context.user_data["source_type"] = "matn"
    status_msg = await update.message.reply_text(tr(context, user_id, "analyzing"))
    await run_analysis(update, context, status_msg)


# ---------------------------------------------------------------------------
# Analysis step
# ---------------------------------------------------------------------------

async def run_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, status_msg):
    user_id = update.effective_user.id
    lang = lang_of(context, user_id)
    text = context.user_data["raw_text"]

    try:
        # AI so'rovi bir necha soniya (ba'zan ko'proq) davom etishi mumkin —
        # bu botning boshqa foydalanuvchilarga/buyruqlarga javob berishini
        # to'smasligi uchun alohida oqimda bajaramiz.
        analysis = await asyncio.to_thread(ai_service.analyze_text, text, lang)
    except Exception as e:
        logger.exception("AI analyze error")
        await status_msg.edit_text(tr(context, user_id, "ai_error", error=str(e)))
        return

    context.user_data["analysis"] = analysis

    msg = tr(
        context,
        user_id,
        "analysis_result",
        minq=analysis.get("min_questions", "-"),
        avgq=analysis.get("avg_questions", "-"),
        maxq=analysis.get("max_questions", "-"),
    )
    topics = analysis.get("topics") or []
    if analysis.get("is_long") and topics:
        msg += "\n\n" + tr(context, user_id, "topics_found") + "\n" + "\n".join(f"• {t}" for t in topics[:20])

    buttons = [[InlineKeyboardButton(tr(context, user_id, "scope_full"), callback_data="scope:full")]]
    if analysis.get("is_long"):
        buttons.append([InlineKeyboardButton(tr(context, user_id, "scope_topic"), callback_data="scope:topic")])
        buttons.append([InlineKeyboardButton(tr(context, user_id, "scope_page"), callback_data="scope:page")])

    await status_msg.edit_text(msg, reply_markup=InlineKeyboardMarkup(buttons))


# ---------------------------------------------------------------------------
# Scope selection (full / topic / page range)
# ---------------------------------------------------------------------------

async def handle_scope(update: Update, context: ContextTypes.DEFAULT_TYPE, scope: str):
    user_id = update.effective_user.id
    context.user_data["scope"] = scope
    query = update.callback_query

    if scope == "full":
        context.user_data["scope_detail"] = ""
        await ask_quantity_edit(query, context, user_id)
    elif scope == "topic":
        topics = context.user_data.get("analysis", {}).get("topics", [])
        context.user_data["topics_list"] = topics
        buttons = [[InlineKeyboardButton(t, callback_data=f"topicpick:{i}")] for i, t in enumerate(topics[:15])]
        buttons.append([InlineKeyboardButton(tr(context, user_id, "back_btn"), callback_data="back")])
        await query.edit_message_text(tr(context, user_id, "choose_topic"), reply_markup=InlineKeyboardMarkup(buttons))
    elif scope == "page":
        context.user_data["awaiting_page_range"] = True
        await query.edit_message_text(tr(context, user_id, "enter_page_range"))


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    analysis = context.user_data.get("analysis")
    if analysis:
        buttons = [[InlineKeyboardButton(tr(context, user_id, "scope_full"), callback_data="scope:full")]]
        if analysis.get("is_long"):
            buttons.append([InlineKeyboardButton(tr(context, user_id, "scope_topic"), callback_data="scope:topic")])
            buttons.append([InlineKeyboardButton(tr(context, user_id, "scope_page"), callback_data="scope:page")])
        await query.edit_message_text(tr(context, user_id, "choose_scope"), reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.edit_message_text(tr(context, user_id, "send_file_or_text"))


# ---------------------------------------------------------------------------
# Question count
# ---------------------------------------------------------------------------

def _qty_buttons(context, user_id):
    analysis = context.user_data.get("analysis", {})
    minq = analysis.get("min_questions", 5)
    avgq = analysis.get("avg_questions", 10)
    maxq = analysis.get("max_questions", 20)
    options = sorted(set([minq, avgq, maxq]))
    buttons = [[InlineKeyboardButton(str(n), callback_data=f"qty:{n}") for n in options]]
    buttons.append([InlineKeyboardButton(tr(context, user_id, "custom_qty"), callback_data="qty:custom")])
    return buttons


async def ask_quantity_edit(query, context, user_id):
    await query.edit_message_text(
        tr(context, user_id, "how_many_questions"),
        reply_markup=InlineKeyboardMarkup(_qty_buttons(context, user_id)),
    )


async def ask_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        tr(context, user_id, "how_many_questions"),
        reply_markup=InlineKeyboardMarkup(_qty_buttons(context, user_id)),
    )


def _difficulty_buttons(context, user_id):
    return [
        [
            InlineKeyboardButton(tr(context, user_id, "diff_easy"), callback_data="diff:easy"),
            InlineKeyboardButton(tr(context, user_id, "diff_medium"), callback_data="diff:medium"),
            InlineKeyboardButton(tr(context, user_id, "diff_hard"), callback_data="diff:hard"),
        ]
    ]


async def handle_qty(update: Update, context: ContextTypes.DEFAULT_TYPE, val: str):
    query = update.callback_query
    user_id = query.from_user.id
    if val == "custom":
        context.user_data["awaiting_custom_qty"] = True
        await query.edit_message_text(tr(context, user_id, "enter_custom_qty"))
        return
    context.user_data["question_count"] = int(val)
    await query.edit_message_text(
        tr(context, user_id, "choose_difficulty"),
        reply_markup=InlineKeyboardMarkup(_difficulty_buttons(context, user_id)),
    )


async def set_quantity_and_ask_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE, qty: int):
    user_id = update.effective_user.id
    context.user_data["question_count"] = qty
    await update.message.reply_text(
        tr(context, user_id, "choose_difficulty"),
        reply_markup=InlineKeyboardMarkup(_difficulty_buttons(context, user_id)),
    )


# ---------------------------------------------------------------------------
# Difficulty selection -> answer format
# ---------------------------------------------------------------------------

async def handle_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE, diff: str):
    query = update.callback_query
    user_id = query.from_user.id
    context.user_data["difficulty"] = diff
    buttons = [
        [
            InlineKeyboardButton("AB", callback_data="fmt:AB"),
            InlineKeyboardButton("ABC", callback_data="fmt:ABC"),
            InlineKeyboardButton("ABCD", callback_data="fmt:ABCD"),
        ]
    ]
    await query.edit_message_text(tr(context, user_id, "choose_answer_format"), reply_markup=InlineKeyboardMarkup(buttons))


# ---------------------------------------------------------------------------
# Answer format + generation (V3: kvota tekshiruvi + xatoda qayta urinish)
# ---------------------------------------------------------------------------

async def _show_quota_exceeded(query, context, user_id):
    buttons = [
        [InlineKeyboardButton(tr(context, user_id, "menu_subscribe"), callback_data="menu:subscribe")],
        [InlineKeyboardButton(tr(context, user_id, "menu_referral"), callback_data="menu:referral")],
        [InlineKeyboardButton(tr(context, user_id, "menu_promo"), callback_data="menu:promo")],
    ]
    await query.edit_message_text(
        tr(context, user_id, "quota_exceeded"),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _run_generation(query, context, user_id, is_regen=False):
    # --- V3: generatsiyadan OLDIN kvota tekshiruvi ---
    allowed, _reason = database.can_generate_test(user_id)
    if not allowed:
        await _show_quota_exceeded(query, context, user_id)
        return

    key = "regenerating" if is_regen else "generating"
    await query.edit_message_text(tr(context, user_id, key))

    text = context.user_data.get("raw_text", "")
    qty = context.user_data.get("question_count", 10)
    fmt = context.user_data.get("answer_format", "ABCD")
    difficulty = context.user_data.get("difficulty", "medium")
    scope_detail = context.user_data.get("scope_detail", "")

    try:
        result = await asyncio.to_thread(
            ai_service.generate_quiz, text, qty, fmt,
            scope_note=scope_detail, difficulty=difficulty,
        )
    except Exception as e:
        # V3: texnik xatolik kvotani YEMAYDI — foydalanuvchiga qayta urinish
        # imkoniyati beriladi.
        logger.exception("AI generate error")
        buttons = [[InlineKeyboardButton(tr(context, user_id, "retry_btn"), callback_data="retry_gen")]]
        await query.edit_message_text(
            tr(context, user_id, "ai_error", error=str(e)),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    questions = result.get("questions", [])
    if not questions:
        buttons = [[InlineKeyboardButton(tr(context, user_id, "retry_btn"), callback_data="retry_gen")]]
        await query.edit_message_text(
            tr(context, user_id, "generation_failed"),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    context.user_data["quiz_result"] = questions
    # Test MUVAFFAQIYATLI tuzilgandan keyingina kvota va statistika yangilanadi.
    database.log_quiz(user_id, len(questions), context.user_data.get("source_type", "matn"), difficulty)
    database.consume_quota(user_id)

    await show_content_choice(query, context, user_id, len(questions))


async def handle_fmt(update: Update, context: ContextTypes.DEFAULT_TYPE, fmt: str):
    query = update.callback_query
    user_id = query.from_user.id
    context.user_data["answer_format"] = fmt
    await _run_generation(query, context, user_id, is_regen=False)


async def handle_regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not context.user_data.get("raw_text"):
        await query.edit_message_text(tr(context, user_id, "nothing_to_export"))
        return
    await _run_generation(query, context, user_id, is_regen=True)


async def handle_retry_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'🔄 Qayta urinish' tugmasi — oldingi urinish texnik xato bergani uchun
    kvota hali ishlatilmagan, shuning uchun oddiy regeneratsiya kabi ishlaydi."""
    query = update.callback_query
    user_id = query.from_user.id
    if not context.user_data.get("raw_text"):
        await query.edit_message_text(tr(context, user_id, "nothing_to_export"))
        return
    await _run_generation(query, context, user_id, is_regen=True)


async def show_content_choice(query, context, user_id, count):
    buttons = [
        [
            InlineKeyboardButton(tr(context, user_id, "content_questions"), callback_data="content:questions"),
            InlineKeyboardButton(tr(context, user_id, "content_answers"), callback_data="content:answers"),
        ],
        [InlineKeyboardButton(tr(context, user_id, "content_both"), callback_data="content:both")],
        [InlineKeyboardButton(tr(context, user_id, "regenerate_btn"), callback_data="regen")],
    ]
    await query.edit_message_text(
        tr(context, user_id, "generated_ok", count=count),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ---------------------------------------------------------------------------
# Content type (savollar / javoblar / ikkalasi) -> output format
# ---------------------------------------------------------------------------

async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE, content: str):
    query = update.callback_query
    user_id = query.from_user.id
    if not context.user_data.get("quiz_result"):
        await query.edit_message_text(tr(context, user_id, "nothing_to_export"))
        return
    context.user_data["pending_content"] = content
    buttons = [
        [
            InlineKeyboardButton(tr(context, user_id, "output_text"), callback_data=f"out:{content}:text"),
            InlineKeyboardButton(tr(context, user_id, "output_docx"), callback_data=f"out:{content}:docx"),
            InlineKeyboardButton(tr(context, user_id, "output_pdf"), callback_data=f"out:{content}:pdf"),
        ],
        [InlineKeyboardButton(tr(context, user_id, "back_btn"), callback_data="back_to_content")],
    ]
    await query.edit_message_text(
        tr(context, user_id, "choose_output_format"),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ---------------------------------------------------------------------------
# Output (matn / docx / pdf) — savollar, javoblar yoki ikkalasi
# ---------------------------------------------------------------------------

def _build_meta(context, user_id, count):
    lang = lang_of(context, user_id)
    return {
        "subtitle": context.user_data.get("scope_detail", "") or tr(context, user_id, "quiz_title"),
        "difficulty": context.user_data.get("difficulty", "medium"),
        "count": count,
        "date": datetime.datetime.now().strftime("%d.%m.%Y"),
        "lang": lang,
    }


async def _send_questions(query, questions, meta, fmt, label):
    if fmt == "text":
        text = branded_output.build_questions_text(questions, meta, tr_label=label)
        for start in range(0, len(text), 3800):
            await query.message.reply_text(text[start:start + 3800])
    elif fmt == "docx":
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            path = tmp.name
        await asyncio.to_thread(branded_output.build_questions_docx, questions, path, meta)
        with open(path, "rb") as f:
            await query.message.reply_document(f, filename="test_savollar.docx")
        os.remove(path)
    elif fmt == "pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            path = tmp.name
        await asyncio.to_thread(branded_output.build_pdf, questions, path, meta, "questions")
        with open(path, "rb") as f:
            await query.message.reply_document(f, filename="test_savollar.pdf")
        os.remove(path)


async def _send_answers(query, questions, meta, fmt, label):
    if fmt == "text":
        text = branded_output.build_answers_text(questions, meta, tr_label=label)
        await query.message.reply_text(text)
    elif fmt == "docx":
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            path = tmp.name
        await asyncio.to_thread(branded_output.build_answers_docx, questions, path, meta)
        with open(path, "rb") as f:
            await query.message.reply_document(f, filename="test_javoblar.docx")
        os.remove(path)
    elif fmt == "pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            path = tmp.name
        await asyncio.to_thread(branded_output.build_pdf, questions, path, meta, "answers")
        with open(path, "rb") as f:
            await query.message.reply_document(f, filename="test_javoblar.pdf")
        os.remove(path)


async def handle_output(update: Update, context: ContextTypes.DEFAULT_TYPE, content: str, fmt: str):
    query = update.callback_query
    user_id = query.from_user.id
    questions = context.user_data.get("quiz_result", [])
    if not questions:
        await query.edit_message_text(tr(context, user_id, "nothing_to_export"))
        return

    meta = _build_meta(context, user_id, len(questions))
    q_label = tr(context, user_id, "label_questions")
    a_label = tr(context, user_id, "label_answers")

    if content in ("questions", "both"):
        await _send_questions(query, questions, meta, fmt, q_label)
    if content in ("answers", "both"):
        await _send_answers(query, questions, meta, fmt, a_label)

    # Natija yuborilgach, foydalanuvchi yana boshqa format/kontent tanlashi
    # yoki qayta generatsiya qilishi mumkin bo'lgan menyuni qayta ko'rsatamiz.
    await show_content_choice(query, context, user_id, len(questions))


# ---------------------------------------------------------------------------
# V3: Obuna (Telegram Stars)
# ---------------------------------------------------------------------------

async def show_subscribe_menu(query, context, user_id):
    buttons = [
        [InlineKeyboardButton(tr(context, user_id, "plan_weekly"), callback_data="buy:weekly")],
        [InlineKeyboardButton(tr(context, user_id, "plan_monthly"), callback_data="buy:monthly")],
        [InlineKeyboardButton(tr(context, user_id, "plan_yearly"), callback_data="buy:yearly")],
        [InlineKeyboardButton(tr(context, user_id, "menu_btn"), callback_data="menu")],
    ]
    await query.edit_message_text(
        tr(context, user_id, "subscribe_title"),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, plan: str):
    query = update.callback_query
    user_id = query.from_user.id
    stars = database.PLAN_STARS.get(plan)
    if not stars:
        return

    plan_label = tr(context, user_id, f"plan_{plan}")
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=plan_label,
        description=plan_label,
        payload=f"sub:{plan}:{user_id}",
        provider_token="",  # Telegram Stars uchun bo'sh qoldiriladi
        currency="XTR",
        prices=[LabeledPrice(plan_label, stars)],
    )


async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    payload_parts = query.invoice_payload.split(":")
    if len(payload_parts) == 3 and payload_parts[0] == "sub" and payload_parts[1] in database.PLAN_DAYS:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Noto'g'ri buyurtma. Qaytadan urinib ko'ring.")


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    user_id = update.effective_user.id
    _, plan, _ = payment.invoice_payload.split(":")

    until = database.grant_subscription(user_id, plan)
    database.log_payment(user_id, payment.total_amount, plan)

    until_str = datetime.datetime.fromisoformat(until).strftime("%d.%m.%Y")
    await update.message.reply_text(tr(context, user_id, "payment_success", until=until_str))
    await show_main_menu_message(update, context, user_id)


# ---------------------------------------------------------------------------
# V3: Mening hisobim
# ---------------------------------------------------------------------------

async def show_account_info(query, context, user_id):
    access = database.get_access_summary(user_id)
    referral_count = database.get_referral_count(user_id)

    lines = [tr(context, user_id, "account_title"), ""]
    lines.append(tr(context, user_id, "account_daily", remaining=access["daily_remaining"]))

    if access["bonus_available"] > 0:
        bonus_date = datetime.datetime.fromisoformat(access["bonus_expires"]).strftime("%d.%m.%Y")
        lines.append(tr(context, user_id, "account_bonus", count=access["bonus_available"], date=bonus_date))
    else:
        lines.append(tr(context, user_id, "account_bonus_none"))

    if access["subscription_active"]:
        until_str = datetime.datetime.fromisoformat(access["subscription_until"]).strftime("%d.%m.%Y")
        plan_label = tr(context, user_id, f"plan_{access['subscription_plan']}").split(" — ")[0]
        lines.append(tr(context, user_id, "account_sub_active", until=until_str, plan=plan_label))
    else:
        lines.append(tr(context, user_id, "account_sub_none"))

    lines.append(tr(context, user_id, "account_referrals", count=referral_count))

    buttons = [
        [InlineKeyboardButton(tr(context, user_id, "menu_subscribe"), callback_data="menu:subscribe")],
        [InlineKeyboardButton(tr(context, user_id, "menu_btn"), callback_data="menu")],
    ]
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))


# ---------------------------------------------------------------------------
# V3: Referral
# ---------------------------------------------------------------------------

async def show_referral_info(query, context, user_id):
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    count = database.get_referral_count(user_id)
    buttons = [[InlineKeyboardButton(tr(context, user_id, "menu_btn"), callback_data="menu")]]
    await query.edit_message_text(
        tr(context, user_id, "referral_info", link=link, count=count),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ---------------------------------------------------------------------------
# V3: Promokod
# ---------------------------------------------------------------------------

async def do_redeem_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.strip().upper()
    success, reason, plan = database.redeem_promo_code(code, user_id)

    if success:
        plan_label = tr(context, user_id, f"plan_{plan}").split(" — ")[0]
        await update.message.reply_text(tr(context, user_id, "promo_success", plan=plan_label))
    else:
        key = {
            "not_found": "promo_not_found",
            "expired": "promo_expired",
            "exhausted": "promo_exhausted",
            "already_used": "promo_already_used",
        }.get(reason, "promo_not_found")
        await update.message.reply_text(tr(context, user_id, key))

    await show_main_menu_message(update, context, user_id)


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    buttons = [
        [InlineKeyboardButton("📊 Statistika", callback_data="admin:stats")],
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin:users")],
        [InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin:broadcast")],
        [InlineKeyboardButton("🎟 Promokod yaratish", callback_data="admin:promo_create")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="admin:settings")],
    ]
    await update.message.reply_text("🔐 Admin panel", reply_markup=InlineKeyboardMarkup(buttons))


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("Ruxsat yo'q", show_alert=True)
        return

    if action == "stats":
        s = database.get_stats()
        top = "\n".join(
            f"  {u['username'] or u['user_id']}: {u['tests_generated']}" for u in s["top_users"]
        ) or "—"
        text = (
            "📊 *Statistika*\n\n"
            f"👥 Jami foydalanuvchilar: {s['total_users']}\n"
            f"📝 Jami yaratilgan testlar: {s['total_tests']}\n"
            f"🟢 Bugun faol: {s['active_today']}\n"
            f"⭐ Jami Stars daromad: {s['total_stars']}\n\n"
            f"🏆 Top foydalanuvchilar:\n{top}"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
    elif action == "users":
        ids = database.all_user_ids()
        await query.edit_message_text(f"👥 Jami {len(ids)} ta foydalanuvchi ro'yxatdan o'tgan.")
    elif action == "broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.edit_message_text("📢 Yubormoqchi bo'lgan xabaringizni yozing:")
    elif action == "promo_create":
        context.user_data["awaiting_admin_promo"] = True
        await query.edit_message_text(tr(context, query.from_user.id, "admin_promo_prompt"))
    elif action == "settings":
        await query.edit_message_text(f"⚙️ Sozlamalar\nSupport: {SUPPORT_USERNAME}\nAdmin ID: {ADMIN_ID}")


async def do_create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data["awaiting_admin_promo"] = False
    parts = update.message.text.strip().split()

    if len(parts) != 3 or parts[1] not in database.PLAN_DAYS or not parts[2].isdigit():
        await update.message.reply_text(tr(context, user_id, "admin_promo_invalid"))
        return

    code, plan, uses = parts[0].upper(), parts[1], int(parts[2])
    database.create_promo_code(code, plan, uses, created_by=user_id)
    await update.message.reply_text(
        tr(context, user_id, "admin_promo_created", code=code, plan=plan, uses=uses)
    )


async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_broadcast"] = False
    text = update.message.text
    ids = database.all_user_ids()
    sent, failed = 0, 0
    status = await update.message.reply_text(f"Yuborilmoqda... 0/{len(ids)}")
    for uid in ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            sent += 1
        except Exception:
            failed += 1
    await status.edit_text(f"✅ Yuborildi: {sent} ta\n❌ Xato: {failed} ta")
