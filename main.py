# Murodjon Soatmurodov tomonidan yaratilgan
import asyncio
import logging
import os

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    PreCheckoutQueryHandler, filters,
)

from config import BOT_TOKEN
import database
import handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Python 3.14 endi asyncio.get_event_loop() ni chaqirilganda avtomatik loop
# yaratmaydi (oldingi versiyalarda yaratardi). python-telegram-bot 21.x hali
# ichkarida shu funksiyaga tayanadi, shuning uchun loopni o'zimiz oldindan
# yaratib qo'yamiz — bu barcha Python versiyalarida (3.9 dan 3.14 gacha)
# xavfsiz ishlaydi.
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("admin", handlers.admin_panel))
    app.add_handler(CommandHandler("cancel", handlers.cancel))

    app.add_handler(CallbackQueryHandler(handlers.on_callback))

    app.add_handler(MessageHandler(filters.Document.ALL, handlers.on_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.on_text))

    # --- V3: Telegram Stars to'lovlari ---
    app.add_handler(PreCheckoutQueryHandler(handlers.precheckout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handlers.successful_payment_handler))

    return app


def main():
    database.init_db()
    app = build_app()

    # --- Ishga tushirish rejimi ---
    # Termux/local'da: USE_WEBHOOK sozlanmagan bo'lsa -> polling (eski xatti-harakat).
    # Render'da (yoki boshqa hostingda): USE_WEBHOOK=1 bo'lsa -> webhook rejimi.
    use_webhook = os.getenv("USE_WEBHOOK", "0") == "1"

    if not use_webhook:
        logging.info("Bot POLLING rejimida ishga tushdi...")
        app.run_polling(allowed_updates=["message", "callback_query", "pre_checkout_query"])
        return

    # --- Webhook rejimi (Render uchun) ---
    port = int(os.getenv("PORT", "10000"))

    # Render bu muhit o'zgaruvchisini avtomatik beradi (masalan
    # https://sizning-bot.onrender.com). Agar boshqa hostingda bo'lsa,
    # WEBHOOK_BASE_URL ni o'zingiz qo'lda kiritishingiz mumkin.
    base_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_BASE_URL")
    if not base_url:
        raise RuntimeError(
            "Webhook rejimi uchun RENDER_EXTERNAL_URL yoki WEBHOOK_BASE_URL "
            "muhit o'zgaruvchisi kerak (masalan: https://sizning-bot.onrender.com)"
        )
    base_url = base_url.rstrip("/")

    # Bot tokenini yashirin yo'l (url_path) sifatida ishlatamiz — shunda
    # boshqa hech kim shu manzilga soxta so'rov yubora olmaydi.
    url_path = BOT_TOKEN
    webhook_url = f"{base_url}/{url_path}"

    logging.info(f"Bot WEBHOOK rejimida ishga tushdi... ({webhook_url})")
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=url_path,
        webhook_url=webhook_url,
        allowed_updates=["message", "callback_query", "pre_checkout_query"],
    )


if __name__ == "__main__":
    main()
