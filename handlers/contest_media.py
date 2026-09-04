# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 📸 RASM/VIDEO BATTLE — ish yuborish, layk bosish, galereya
══════════════════════════════════════════════════════════
"""
import logging

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ContextTypes, filters

import config
import texts
from database import db
from keyboards import kb_media_like, kb_media_gallery

logger = logging.getLogger(__name__)


async def _display_name(user_id: int) -> str:
    u = await db.get_user(user_id)
    if u and u.get("username"):
        return f"@{u['username']}"
    if u and u.get("first_name"):
        return u["first_name"]
    return f"ID{user_id}"


async def on_media_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi shaxsiy chatda rasm/video yuborganda ishlaydi."""
    contest_id = context.user_data.get("awaiting_media_contest")
    if not contest_id:
        return  # kutilayotgan konkurs yo'q — boshqa handlerlarga tegishli bo'lishi mumkin

    msg = update.message
    user = update.effective_user

    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active" or contest.get("type") != "media":
        context.user_data.pop("awaiting_media_contest", None)
        return

    if not await db.is_participant(contest_id, user.id):
        await msg.reply_text(texts.MEDIA_NOT_JOINED_FOR_SUBMIT)
        return

    existing = await db.get_submission_by_user(contest_id, user.id)
    if existing:
        await msg.reply_text(texts.MEDIA_ALREADY_SUBMITTED)
        context.user_data.pop("awaiting_media_contest", None)
        return

    if msg.photo:
        file_id = msg.photo[-1].file_id
        media_type = "photo"
    elif msg.video:
        file_id = msg.video.file_id
        media_type = "video"
    else:
        await msg.reply_text(texts.MEDIA_SUBMISSION_REJECTED)
        return

    name = await _display_name(user.id)
    caption = texts.MEDIA_CAPTION.format(name=name, likes=0)

    try:
        if media_type == "photo":
            sent = await context.bot.send_photo(
                contest["chat_id"], file_id, caption=caption,
                reply_markup=kb_media_like(contest_id, 0, 0),
            )
        else:
            sent = await context.bot.send_video(
                contest["chat_id"], file_id, caption=caption,
                reply_markup=kb_media_like(contest_id, 0, 0),
            )
    except Exception as e:
        logger.error(f"Media postini joylashda xato: {e}")
        await msg.reply_text("❌ Ishingizni kanalga joylashda xatolik yuz berdi. Admin bilan bog'laning.")
        return

    sub_id = await db.create_submission(
        contest_id, user.id, file_id, media_type, contest["chat_id"], sent.message_id
    )
    if sub_id is None:
        try:
            await sent.delete()
        except Exception:
            pass
        await msg.reply_text(texts.MEDIA_ALREADY_SUBMITTED)
        context.user_data.pop("awaiting_media_contest", None)
        return

    try:
        await context.bot.edit_message_reply_markup(
            chat_id=contest["chat_id"], message_id=sent.message_id,
            reply_markup=kb_media_like(contest_id, sub_id, 0),
        )
    except Exception:
        pass

    context.user_data.pop("awaiting_media_contest", None)
    await msg.reply_text(texts.MEDIA_SUBMISSION_ACCEPTED)


async def on_media_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    submission_id = int(query.data.split("_")[1])

    sub = await db.get_submission(submission_id)
    if not sub:
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return

    contest = await db.get_contest(sub["contest_id"])
    if not contest or contest["status"] != "active":
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return

    if sub["user_id"] == user.id:
        await query.answer(texts.MEDIA_LIKE_OWN, show_alert=True)
        return

    liked = await db.like_submission(submission_id, user.id)
    if not liked:
        await query.answer(texts.MEDIA_LIKE_ALREADY, show_alert=True)
        return

    await query.answer(texts.MEDIA_LIKE_SUCCESS)
    sub = await db.get_submission(submission_id)
    try:
        await query.edit_message_reply_markup(
            reply_markup=kb_media_like(sub["contest_id"], submission_id, sub["likes_count"])
        )
    except BadRequest:
        pass
    try:
        name = await _display_name(sub["user_id"])
        await context.bot.edit_message_caption(
            chat_id=sub["chat_id"], message_id=sub["message_id"],
            caption=texts.MEDIA_CAPTION.format(name=name, likes=sub["likes_count"]),
            reply_markup=kb_media_like(sub["contest_id"], submission_id, sub["likes_count"]),
        )
    except Exception:
        pass


async def _build_gallery(contest_id: int, page: int):
    rows, total_pages, page = await db.submissions_page(contest_id, page, config.MEDIA_GALLERY_PER_PAGE)
    items = []
    for r in rows:
        name = await _display_name(r["user_id"])
        items.append({"id": r["id"], "user_id": r["user_id"], "likes_count": r["likes_count"], "display_name": name})
    return items, total_pages, page


async def on_media_gallery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'🖼 Ishlarni ko'rish' — DM da ro'yxat ko'rsatiladi (vote ro'yxatiga o'xshash)."""
    query = update.callback_query
    parts = query.data.split("_")
    contest_id, page = int(parts[1]), int(parts[2])
    user = update.effective_user
    in_dm = update.effective_chat and update.effective_chat.type == "private"

    contest = await db.get_contest(contest_id)
    if not contest:
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return

    items, total_pages, page = await _build_gallery(contest_id, page)
    if not items:
        await query.answer("📭 Hozircha ishlar yo'q.", show_alert=True)
        return

    kb = kb_media_gallery(contest_id, items, page, total_pages)
    header = "🖼 <b>Ishlar ro'yxati</b>\n\nKo'rish uchun bosing:"

    if in_dm:
        await query.answer()
        await query.edit_message_text(header, parse_mode="HTML", reply_markup=kb)
        return

    try:
        await context.bot.send_message(user.id, header, parse_mode="HTML", reply_markup=kb)
        await query.answer("📩 Ishlar ro'yxati shaxsiy xabarda yuborildi!")
    except Exception:
        me = await context.bot.get_me()
        await query.answer(
            f"❌ Avval botni ishga tushiring: @{me.username} ga /start yozing.", show_alert=True
        )


async def on_media_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Galereyadan bitta ishni ko'rish — DM ga nusxa yuboriladi, layk tugmasi bilan."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    contest_id, submission_id = int(parts[1]), int(parts[2])

    sub = await db.get_submission(submission_id)
    if not sub:
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return

    try:
        await context.bot.copy_message(
            chat_id=update.effective_user.id,
            from_chat_id=sub["chat_id"],
            message_id=sub["message_id"],
            reply_markup=kb_media_like(contest_id, submission_id, sub["likes_count"]),
        )
    except Exception as e:
        logger.warning(f"Media nusxalashda xato: {e}")
        await context.bot.send_message(update.effective_user.id, "❌ Ishni ko'rsatib bo'lmadi.")


def register(app: Application):
    app.add_handler(CallbackQueryHandler(on_media_like, pattern="^mlike_"))
    app.add_handler(CallbackQueryHandler(on_media_gallery, pattern="^mgallery_\\d+_\\d+$"))
    app.add_handler(CallbackQueryHandler(on_media_view, pattern="^mview_"))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & (filters.PHOTO | filters.VIDEO), on_media_submission
    ))
