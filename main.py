# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 BB_BOT PRO — asosiy ishga tushirish fayli
══════════════════════════════════════════════════════════
 Ishga tushirish:
    1. .env faylini to'ldiring (BOT_TOKEN, ADMIN_IDS)
    2. pip install -r requirements.txt
    3. python main.py
══════════════════════════════════════════════════════════
"""
import asyncio
import logging

from telegram.ext import Application, ApplicationBuilder

import config
from database import db
from handlers import register_all
from handlers.contest_join import resume_all_monitors, resume_scheduled_publishes

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler(config.LOG_FILE, encoding="utf-8")],
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    await db.connect(config.DB_PATH)
    await resume_all_monitors(application)
    await resume_scheduled_publishes(application)
    logger.info("Bot to'liq ishga tushdi ✅")


async def post_shutdown(application: Application):
    await db.close()


def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise SystemExit(
            "❌ BOT_TOKEN sozlanmagan! .env faylida yoki config.py da BOT_TOKEN ni kiriting."
        )

    app = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    register_all(app)

    logger.info("Polling boshlandi...")
    app.run_polling(
        allowed_updates=["message", "callback_query", "pre_checkout_query", "message_reaction"]
    )


if __name__ == "__main__":
    main()
