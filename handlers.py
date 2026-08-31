import os
import logging
import tempfile

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database
import file_parser
import ai_service
from export_docx import build_quiz_docx
from locales import T
from config import ADMIN_ID, SUPPORT_USERNAME, MAX_FILE_SIZE_MB, TEMP_MESSAGE_TTL

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
# /start and language selection
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    database.upsert_user(user.id, user.username, user.full_name)
    context.user_data.clear()
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
# Callback router
# ---------------------------------------------------------------------------

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("lang:"):
        await handle_lang(update, context, data.split(":", 1)[1])
    elif data.startswith("scope:"):
        await handle_scope(update, context, data.split(":", 1)[1])
    elif data.startswith("topicpick:"):
        idx = int(data.split(":", 1)[1])
        topics = context.user_data.get("topics_list", [])
        context.user_data["scope_detail"] = topics[idx] if idx < len(topics) else ""
        await ask_quantity_edit(query, context, user_id)
    elif data.startswith("qty:"):
        await handle_qty(update, context, data.split(":", 1)[1])
    elif data.startswith("fmt:"):
        await handle_fmt(update, context, data.split(":", 1)[1])
    elif data.startswith("output:"):
        await handle_output(update, context, data.split(":", 1)[1])
    elif data == "back":
        await handle_back(update, context)
    elif data.startswith("admin:"):
        await handle_admin_callback(update, context, data.split(":", 1)[1])


async def handle_lang(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    user_id = update.effective_user.id
    context.user_data["language"] = lang
    database.set_language(user_id, lang)
    query = update.callback_query
    await query.edit_message_text(tr(context, user_id, "welcome"))


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
        text = file_parser.extract_text(tmp_path, ext)
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

    # Admin broadcast flow
    if context.user_data.get("awaiting_broadcast") and user_id == ADMIN_ID:
        await do_broadcast(update, context)
        return

    # Custom question count flow
    if context.user_data.get("awaiting_custom_qty"):
        txt = update.message.text.strip()
        if txt.isdigit() and int(txt) > 0:
            context.user_data["awaiting_custom_qty"] = False
            await set_quantity_and_ask_format(update, context, int(txt))
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
        analysis = ai_service.analyze_text(text, lang)
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


async def handle_qty(update: Update, context: ContextTypes.DEFAULT_TYPE, val: str):
    query = update.callback_query
    user_id = query.from_user.id
    if val == "custom":
        context.user_data["awaiting_custom_qty"] = True
        await query.edit_message_text(tr(context, user_id, "enter_custom_qty"))
        return
    context.user_data["question_count"] = int(val)
    buttons = [
        [
            InlineKeyboardButton("AB", callback_data="fmt:AB"),
            InlineKeyboardButton("ABC", callback_data="fmt:ABC"),
            InlineKeyboardButton("ABCD", callback_data="fmt:ABCD"),
        ]
    ]
    await query.edit_message_text(tr(context, user_id, "choose_answer_format"), reply_markup=InlineKeyboardMarkup(buttons))


async def set_quantity_and_ask_format(update: Update, context: ContextTypes.DEFAULT_TYPE, qty: int):
    user_id = update.effective_user.id
    context.user_data["question_count"] = qty
    buttons = [
        [
            InlineKeyboardButton("AB", callback_data="fmt:AB"),
            InlineKeyboardButton("ABC", callback_data="fmt:ABC"),
            InlineKeyboardButton("ABCD", callback_data="fmt:ABCD"),
        ]
    ]
    await update.message.reply_text(tr(context, user_id, "choose_answer_format"), reply_markup=InlineKeyboardMarkup(buttons))


# ---------------------------------------------------------------------------
# Answer format + generation
# ---------------------------------------------------------------------------

async def handle_fmt(update: Update, context: ContextTypes.DEFAULT_TYPE, fmt: str):
    query = update.callback_query
    user_id = query.from_user.id
    context.user_data["answer_format"] = fmt
    await query.edit_message_text(tr(context, user_id, "generating"))

    lang = lang_of(context, user_id)
    text = context.user_data.get("raw_text", "")
    qty = context.user_data.get("question_count", 10)
    scope_detail = context.user_data.get("scope_detail", "")

    try:
        result = ai_service.generate_quiz(text, lang, qty, fmt, scope_note=scope_detail)
    except Exception as e:
        logger.exception("AI generate error")
        await query.edit_message_text(tr(context, user_id, "ai_error", error=str(e)))
        return

    questions = result.get("questions", [])
    if not questions:
        await query.edit_message_text(tr(context, user_id, "generation_failed"))
        return

    context.user_data["quiz_result"] = questions
    database.log_quiz(user_id, len(questions), context.user_data.get("source_type", "matn"))

    buttons = [
        [
            InlineKeyboardButton(tr(context, user_id, "output_text"), callback_data="output:text"),
            InlineKeyboardButton(tr(context, user_id, "output_docx"), callback_data="output:docx"),
        ]
    ]
    await query.edit_message_text(
        tr(context, user_id, "generated_ok", count=len(questions)),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ---------------------------------------------------------------------------
# Output (text / docx)
# ---------------------------------------------------------------------------

async def handle_output(update: Update, context: ContextTypes.DEFAULT_TYPE, fmt: str):
    query = update.callback_query
    user_id = query.from_user.id
    questions = context.user_data.get("quiz_result", [])
    if not questions:
        await query.edit_message_text(tr(context, user_id, "nothing_to_export"))
        return

    if fmt == "text":
        lines = []
        for i, q in enumerate(questions, start=1):
            lines.append(f"{i}. {q['question']}")
            for k, v in q["options"].items():
                lines.append(f"   {k}) {v}")
        answers = ", ".join(f"{i + 1}-{q['correct']}" for i, q in enumerate(questions))
        lines.append("")
        lines.append(tr(context, user_id, "answers_label") + ": " + answers)
        full = "\n".join(lines)
        for start in range(0, len(full), 3800):
            await query.message.reply_text(full[start:start + 3800])
    else:
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            path = tmp.name
        build_quiz_docx(questions, path, title=tr(context, user_id, "quiz_title"))
        with open(path, "rb") as f:
            await query.message.reply_document(f, filename="test.docx")
        os.remove(path)


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
            f"🟢 Bugun faol: {s['active_today']}\n\n"
            f"🏆 Top foydalanuvchilar:\n{top}"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
    elif action == "users":
        ids = database.all_user_ids()
        await query.edit_message_text(f"👥 Jami {len(ids)} ta foydalanuvchi ro'yxatdan o'tgan.")
    elif action == "broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.edit_message_text("📢 Yubormoqchi bo'lgan xabaringizni yozing:")
    elif action == "settings":
        await query.edit_message_text(f"⚙️ Sozlamalar\nSupport: {SUPPORT_USERNAME}\nAdmin ID: {ADMIN_ID}")


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
