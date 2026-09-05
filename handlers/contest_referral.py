# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 👥 REFERAL — shaxsiy taklif havolasini generatsiya qilish
══════════════════════════════════════════════════════════
"""
import logging

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

import config
import texts
from database import db

logger = logging.getLogger(__name__)


async def on_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    contest_id = int(query.data.split("_")[1])

    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active":
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return

    if not await db.is_participant(contest_id, user.id):
        await query.answer(texts.REFERRAL_NOT_JOINED, show_alert=True)
        return

    me = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{contest_id}_{user.id}"
    count = await db.count_referrals(contest_id, user.id)

    try:
        await context.bot.send_message(
            user.id,
            texts.REFERRAL_LINK_TEXT.format(link=link, points=config.REFERRAL_POINTS, count=count),
            parse_mode="HTML",
        )
        await query.answer("📩 Taklif havolangiz shaxsiy xabarda yuborildi!")
    except Exception:
        await query.answer(
            "❌ Avval pastdagi \"🤖 Botni ishga tushirish\" tugmasini bosing, so'ng qaytadan urinib ko'ring.",
            show_alert=True,
        )


def register(app: Application):
    app.add_handler(CallbackQueryHandler(on_referral_link, pattern="^creflink_"))
