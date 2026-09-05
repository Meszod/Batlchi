# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 PRO OBUNA — Telegram Stars (XTR) orqali to'lov
 Alohida merchant/provider token kerak emas — Telegram
 Stars to'g'ridan-to'g'ri Bot API orqali ishlaydi.
══════════════════════════════════════════════════════════
"""
import logging
import time

from telegram import Update, LabeledPrice
from telegram.ext import (
    Application, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler,
    ContextTypes, filters,
)

import config
import texts
from database import db
from keyboards import kb_pro_plans
from utils import format_dt

logger = logging.getLogger(__name__)


async def on_pro_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await db.is_pro(user_id):
        u = await db.get_user(user_id)
        until = format_dt(u["pro_until"])
        await update.message.reply_text(
            texts.PRO_ALREADY.format(until=until), parse_mode="HTML", reply_markup=kb_pro_plans()
        )
        return
    await update.message.reply_text(texts.PRO_INFO, parse_mode="HTML", reply_markup=kb_pro_plans())


async def on_buy_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan_key = query.data.split("_", 1)[1]
    plan = config.PRO_PLANS.get(plan_key)
    if not plan:
        await query.answer("❌ Noto'g'ri tarif.", show_alert=True)
        return

    prices = [LabeledPrice(label=plan["title"], amount=plan["stars"])]
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=plan["title"],
        description=f"BB_bot PRO obuna — {plan['days']} kunlik",
        payload=f"prosub:{plan_key}:{update.effective_user.id}",
        provider_token="",  # Telegram Stars uchun bo'sh qoldiriladi
        currency="XTR",
        prices=prices,
    )


async def on_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("prosub:") or query.invoice_payload.startswith("starsvote:"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Noma'lum to'lov turi.")


async def on_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload_parts = payment.invoice_payload.split(":")

    if payload_parts[0] == "prosub" and len(payload_parts) == 3:
        plan_key = payload_parts[1]
        plan = config.PRO_PLANS.get(plan_key)
        if not plan:
            return
        user_id = update.effective_user.id
        await db.set_pro(user_id, plan["days"])
        await update.message.reply_text(
            texts.PRO_PURCHASED.format(days=plan["days"]), parse_mode="HTML"
        )
        logger.info(f"PRO sotib olindi: user={user_id} plan={plan_key}")

    elif payload_parts[0] == "starsvote" and len(payload_parts) == 3:
        contest_id, user_id = int(payload_parts[1]), int(payload_parts[2])
        contest = await db.get_contest(contest_id)
        if not contest or contest["status"] != "active":
            await update.message.reply_text("❌ Bu konkurs allaqachon yakunlangan, ball berilmadi.")
            return
        await db.add_point_event(contest_id, user_id, "stars", config.STARS_VOTE_POINTS, once=False)
        await update.message.reply_text(
            texts.STARS_SUCCESS.format(points=config.STARS_VOTE_POINTS), parse_mode="HTML"
        )
        from handlers.contest_join import _refresh_post
        await _refresh_post(context, contest_id)
        logger.info(f"Stars ovoz: user={user_id} contest={contest_id}")


def register(app: Application):
    app.add_handler(MessageHandler(filters.Regex("^💎 PRO$"), on_pro_button))
    app.add_handler(CallbackQueryHandler(on_buy_pro, pattern="^buypro_"))
    app.add_handler(PreCheckoutQueryHandler(on_pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, on_successful_payment))
