# -*- coding: utf-8 -*-
"""/start, asosiy menyu, yordam bo'limi."""
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

import config
import texts
from database import db
from keyboards import kb_main_menu

logger = logging.getLogger(__name__)


def is_super_admin(user_id: int) -> bool:
    return user_id in config.SUPER_ADMIN_IDS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if await db.is_banned(user.id):
        await update.message.reply_text("🚫 Siz bloklangansiz.")
        return
    is_new = await db.upsert_user(user.id, user.username or "", user.first_name or "")
    if is_new:
        logger.info(f"Yangi foydalanuvchi: {user.id}")

    # 👥 Referal deep-link: /start ref_<contest_id>_<referrer_id>
    if context.args:
        payload = context.args[0]
        if payload.startswith("ref_"):
            parts = payload.split("_")
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                contest_id, referrer_id = int(parts[1]), int(parts[2])
                if referrer_id != user.id:
                    context.user_data["pending_referral"] = {
                        "contest_id": contest_id, "referrer_id": referrer_id,
                    }
                    referrer = await db.get_user(referrer_id)
                    ref_name = (
                        f"@{referrer['username']}" if referrer and referrer.get("username")
                        else (referrer["first_name"] if referrer else "do'stingiz")
                    )
                    await update.message.reply_text(
                        texts.REFERRAL_WELCOME_NUDGE.format(name=ref_name), parse_mode="HTML"
                    )

    await update.message.reply_text(
        texts.WELCOME.format(name=user.first_name or "foydalanuvchi"),
        parse_mode="HTML",
        reply_markup=kb_main_menu(is_admin=is_super_admin(user.id)),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(texts.HELP_TEXT, parse_mode="HTML")


async def on_help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_help(update, context)


async def on_unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply-menyudagi tugmalar bosilganda, agar boshqa handler ushlamasa shu yerga tushadi."""
    return  # boshqa ConversationHandlerlar ushlaydi; bu yerda hech narsa qilmaymiz


def register(app: Application):
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Yordam$"), on_help_button))
