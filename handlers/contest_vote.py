# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 🗳 OVOZ TO'PLASH — nomzodlar ro'yxati va ovoz berish
 Ro'yxat foydalanuvchining shaxsiy (DM) chatida ko'rsatiladi —
 kanal/guruh postini har bir bosishda o'zgartirmaslik uchun.
══════════════════════════════════════════════════════════
"""
import logging

from telegram import Update
from telegram.error import Forbidden, BadRequest
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

import config
import texts
from database import db
from keyboards import kb_vote_candidates

logger = logging.getLogger(__name__)


def _channel_link(chat_id: int, message_id: int):
    """Konkurs postiga to'g'ridan-to'g'ri olib boruvchi havola (kanal ichidagi post)."""
    if not chat_id or not message_id:
        return None
    cid = str(chat_id)
    if cid.startswith("-100"):
        cid = cid[4:]
    elif cid.startswith("-"):
        cid = cid[1:]
    return f"https://t.me/c/{cid}/{message_id}"


async def _candidate_display_name(user_id: int) -> str:
    u = await db.get_user(user_id)
    if u and u.get("username"):
        return f"@{u['username']}"
    if u and u.get("first_name"):
        return u["first_name"]
    return f"ID{user_id}"


async def _build_candidates_list(contest_id: int, page: int):
    rows, total_pages, page = await db.candidates_page(contest_id, page, config.VOTE_CANDIDATES_PER_PAGE)
    candidates = []
    for r in rows:
        name = await _candidate_display_name(r["user_id"])
        candidates.append({"user_id": r["user_id"], "points": r["points"], "display_name": name})
    return candidates, total_pages, page


async def on_vote_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'🗳 Ovoz berish' tugmasi. Kanal/guruhda bosilsa — DM ga yangi xabar yuboradi.
    DM ichida (sahifalashda) bosilsa — mavjud xabarni tahrirlaydi."""
    query = update.callback_query
    parts = query.data.split("_")
    contest_id, page = int(parts[1]), int(parts[2])
    user = update.effective_user
    in_dm = update.effective_chat and update.effective_chat.type == "private"

    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active":
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        if in_dm:
            await query.edit_message_text(texts.JOIN_FINISHED)
        return

    candidates, total_pages, page = await _build_candidates_list(contest_id, page)
    if not candidates:
        await query.answer(texts.VOTE_LIST_EMPTY, show_alert=True)
        if in_dm:
            await query.edit_message_text(texts.VOTE_LIST_EMPTY)
        return

    channel_url = _channel_link(contest["chat_id"], contest["message_id"])
    kb = kb_vote_candidates(contest_id, candidates, page, total_pages, channel_url)

    if in_dm:
        await query.answer()
        await query.edit_message_text(texts.VOTE_LIST_HEADER, parse_mode="HTML", reply_markup=kb)
        return

    try:
        await context.bot.send_message(
            user.id, texts.VOTE_LIST_HEADER, parse_mode="HTML", reply_markup=kb
        )
        await query.answer("📩 Nomzodlar ro'yxati sizga shaxsiy xabarda yuborildi!")
    except Forbidden:
        await query.answer(
            "❌ Avval pastdagi \"🤖 Botni ishga tushirish\" tugmasini bosing, so'ng qaytadan urinib ko'ring.",
            show_alert=True,
        )


async def on_vote_cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split("_")
    contest_id, candidate_id = int(parts[1]), int(parts[2])
    voter = update.effective_user

    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active":
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return

    if not await db.is_participant(contest_id, voter.id):
        await query.answer(texts.VOTE_NOT_JOINED, show_alert=True)
        return

    if voter.id == candidate_id:
        await query.answer(texts.VOTE_SELF, show_alert=True)
        return

    result = await db.cast_vote(contest_id, voter.id, candidate_id)
    text_map = {"new": texts.VOTE_NEW, "changed": texts.VOTE_CHANGED, "same": texts.VOTE_SAME}
    await query.answer(text_map[result], show_alert=True)

    # ro'yxatni yangilangan ovozlar bilan qayta chizamiz (0-sahifadan boshlab)
    try:
        candidates, total_pages, page = await _build_candidates_list(contest_id, 0)
        channel_url = _channel_link(contest["chat_id"], contest["message_id"])
        kb = kb_vote_candidates(contest_id, candidates, page, total_pages, channel_url)
        await query.edit_message_reply_markup(reply_markup=kb)
    except BadRequest:
        pass


async def on_vote_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.edit_message_text("✅ Yopildi. Qayta ochish uchun kanal postidagi tugmani bosing.")
    except Exception:
        pass


async def on_noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


def register(app: Application):
    app.add_handler(CallbackQueryHandler(on_vote_cast, pattern="^vcand_"))
    app.add_handler(CallbackQueryHandler(on_vote_list, pattern="^vlist_\\d+_\\d+$"))
    app.add_handler(CallbackQueryHandler(on_vote_close, pattern="^vclose_"))
    app.add_handler(CallbackQueryHandler(on_noop, pattern="^noop$"))
