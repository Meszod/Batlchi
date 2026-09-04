# -*- coding: utf-8 -*-
"""Foydalanuvchi — o'z konkurslarini boshqarishi (yakunlash, cho'zish, reyting)."""
import logging
import time

from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters,
)

from database import db
from keyboards import kb_my_contests, kb_contest_manage, kb_extend_options, kb_back
from utils import format_duration, format_remaining, format_dt
from handlers.contest_join import unschedule_contest_monitor, draw_and_announce_winners

logger = logging.getLogger(__name__)


async def on_my_contests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    contests = await db.contests_by_owner(user_id)
    if not contests:
        await update.message.reply_text("📭 Sizda hali konkurs mavjud emas.")
        return
    await update.message.reply_text(
        "📋 <b>Mening konkurslarim</b>\n\nKerakli konkursni tanlang:",
        parse_mode="HTML",
        reply_markup=kb_my_contests(contests),
    )


async def _render_contest_view(query, contest_id: int):
    contest = await db.get_contest(contest_id)
    if not contest:
        await query.edit_message_text("❌ Konkurs topilmadi.")
        return
    count = await db.count_participants(contest_id)
    remaining = contest["end_time"] - time.time() if contest["status"] == "active" else 0
    status_map = {"active": "🟢 Faol", "finished": "🔴 Yakunlangan", "cancelled": "⚪️ Bekor qilingan"}

    text = (
        f"📺 <b>{contest['chat_title']}</b>\n\n"
        f"🆔 Konkurs: #{contest['id']}\n"
        f"📊 Holat: {status_map.get(contest['status'], contest['status'])}\n"
        f"👥 Ishtirokchilar: {count}\n"
        f"🏆 G'oliblar soni: {contest['winners_count']} (ball reytingi bo'yicha)\n"
        f"⏰ Davomiylik: {format_duration(contest['duration_minutes'])}\n"
        f"🚀 Boost bonusi: {'✅ Yoqilgan (+ball)' if contest['require_boost'] else '❌ Yo\u02bbq'}\n"
    )
    if contest["status"] == "active":
        text += f"⏳ Qolgan vaqt: {format_remaining(remaining)}\n"
    text += f"📅 Yaratilgan: {format_dt(contest['created_at'])}\n"

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=kb_contest_manage(contest_id, contest["status"], bool(contest["require_boost"])),
    )


async def on_view_contest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    contest_id = int(query.data.split("_")[2])
    contest = await db.get_contest(contest_id)
    if not contest or contest["owner_id"] != update.effective_user.id:
        await query.answer("❌ Bu sizning konkursingiz emas!", show_alert=True)
        return
    await _render_contest_view(query, contest_id)


async def on_back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    contests = await db.contests_by_owner(update.effective_user.id)
    if not contests:
        await query.edit_message_text("📭 Sizda hali konkurs mavjud emas.")
        return
    await query.edit_message_text(
        "📋 <b>Mening konkurslarim</b>\n\nKerakli konkursni tanlang:",
        parse_mode="HTML",
        reply_markup=kb_my_contests(contests),
    )


async def on_stop_contest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Konkursni muddatidan oldin yakunlaydi — g'oliblar ball reytingi bo'yicha avtomatik aniqlanadi."""
    query = update.callback_query
    contest_id = int(query.data.split("_")[2])
    contest = await db.get_contest(contest_id)
    if not contest or contest["owner_id"] != update.effective_user.id:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    if contest["status"] != "active":
        await query.answer("ℹ️ Bu konkurs allaqachon yakunlangan.", show_alert=True)
        return
    await query.answer("🏁 Konkurs yakunlanmoqda, g'oliblar aniqlanmoqda...")
    await draw_and_announce_winners(context, contest_id, reason="admin tomonidan muddatidan oldin yakunlandi")
    await _render_contest_view(query, contest_id)


async def on_extend_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    contest_id = int(query.data.split("_")[2])
    await query.edit_message_text(
        "➕ Qancha vaqt qo'shmoqchisiz?", reply_markup=kb_extend_options(contest_id)
    )


async def on_extend_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split("_")
    contest_id = int(parts[1])
    minutes = int(parts[2])
    contest = await db.get_contest(contest_id)
    if not contest or contest["owner_id"] != update.effective_user.id:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    is_pro = await db.is_pro(update.effective_user.id)
    import config
    max_allowed = config.PRO_MAX_DURATION_MINUTES if is_pro else config.FREE_MAX_DURATION_MINUTES
    new_end = max(contest["end_time"], time.time()) + minutes * 60
    total_duration_min = (new_end - contest["start_time"]) / 60
    if total_duration_min > max_allowed:
        await query.answer(
            "❌ Bepul foydalanuvchilar uchun umumiy davomiylik 7 kundan oshmasligi kerak! "
            "PRO xizmatini soting oling.", show_alert=True,
        )
        return

    await db.update_contest(contest_id, end_time=new_end)
    await query.answer("✅ Vaqt cho'zildi!", show_alert=True)
    try:
        await context.bot.send_message(
            contest["chat_id"],
            f"⏰ Konkurs vaqti <b>{format_duration(minutes)}</b>ga uzaytirildi!",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await _render_contest_view(query, contest_id)


async def on_remove_boost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    contest_id = int(query.data.split("_")[2])
    contest = await db.get_contest(contest_id)
    if not contest or contest["owner_id"] != update.effective_user.id:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await db.update_contest(contest_id, require_boost=0, boost_chat_id=None, boost_link=None)
    await query.answer("✅ Boost bonusi o'chirildi.", show_alert=True)
    await _render_contest_view(query, contest_id)


async def on_leaderboard_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    contest_id = int(query.data.split("_")[2])
    contest = await db.get_contest(contest_id)
    if not contest or contest["owner_id"] != update.effective_user.id:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await query.answer()

    top = await db.leaderboard(contest_id, limit=50)
    winners = await db.contest_winners(contest_id)
    winner_positions = {w["user_id"]: w["position"] for w in winners}

    if not top:
        await query.edit_message_text(
            "📊 Hozircha ishtirokchilar yo'q.", reply_markup=kb_back(f"mc_view_{contest_id}")
        )
        return

    lines = []
    for i, p in enumerate(top, 1):
        u = await db.get_user(p["user_id"])
        uname = f"@{u['username']}" if u and u.get("username") else f"ID{p['user_id']}"
        mark = f" 🏆{winner_positions[p['user_id']]}" if p["user_id"] in winner_positions else ""
        boost_mark = " 🚀" if p["boosted"] else ""
        lines.append(f"{i}. {uname} — {p['points']} ball{boost_mark}{mark}")

    title = "📊 <b>Reyting / Natijalar</b>" if contest["status"] != "active" else "📊 <b>Joriy reyting</b>"
    text = f"{title}\n\n" + "\n".join(lines[:50])
    await query.edit_message_text(
        text[:4000], parse_mode="HTML", reply_markup=kb_back(f"mc_view_{contest_id}")
    )


def register(app: Application):
    app.add_handler(MessageHandler(filters.Regex("^📋 Mening konkurslarim$"), on_my_contests))
    app.add_handler(CallbackQueryHandler(on_view_contest, pattern="^mc_view_"))
    app.add_handler(CallbackQueryHandler(on_back_to_list, pattern="^mc_back$"))
    app.add_handler(CallbackQueryHandler(on_stop_contest, pattern="^mc_stop_"))
    app.add_handler(CallbackQueryHandler(on_remove_boost, pattern="^mc_noboost_"))
    app.add_handler(CallbackQueryHandler(on_extend_menu, pattern="^mc_extend_"))
    app.add_handler(CallbackQueryHandler(on_extend_apply, pattern="^mcext_"))
    app.add_handler(CallbackQueryHandler(on_leaderboard_view, pattern="^mc_lead_"))
