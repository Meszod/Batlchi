# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 SUPER ADMIN PANEL
 Faqat config.SUPER_ADMIN_IDS ro'yxatidagi foydalanuvchilar
 kira oladi. Global majburiy kanallar, foydalanuvchilar,
 statistika, broadcast va PRO boshqaruvi shu yerda.
══════════════════════════════════════════════════════════
"""
import logging
import time

from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters,
    ConversationHandler, CommandHandler,
)

import config
import texts
from database import db
from keyboards import (
    kb_admin_main, kb_admin_channels, kb_admin_users, kb_admin_pro, kb_back, kb_main_menu,
)
from utils import get_chat_from_forward, is_bot_admin_in_chat, get_chat_invite_link

logger = logging.getLogger(__name__)

WAIT_ADD_CHANNEL, WAIT_BAN_ID, WAIT_UNBAN_ID, WAIT_WARN_ID, WAIT_INFO_ID = range(5)
WAIT_BROADCAST, WAIT_GRANT_PRO, WAIT_REVOKE_PRO = range(5, 8)


def is_super_admin(user_id: int) -> bool:
    return user_id in config.SUPER_ADMIN_IDS


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_super_admin(update.effective_user.id):
        await update.message.reply_text(texts.NO_PERMISSION)
        return
    await update.message.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())


async def on_admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())


# ══════════════════════════════════════════════════════
# GLOBAL MAJBURIY KANALLAR
# ══════════════════════════════════════════════════════
async def on_channels_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channels = await db.list_global_channels()
    text = "🌍 <b>Global majburiy kanallar</b>\n\n"
    text += "Bu kanallar barcha (PRO bo'lmagan) konkurslarda avtomatik majburiy bo'lib qo'shiladi.\n\n"
    if channels:
        text += "\n".join(f"• {c['title']}" for c in channels)
    else:
        text += "Hozircha kanal yo'q."
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb_admin_channels(channels))


async def on_delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = int(query.data.split("_")[2])
    await db.remove_global_channel(chat_id)
    await query.answer("✅ O'chirildi")
    channels = await db.list_global_channels()
    text = "🌍 <b>Global majburiy kanallar</b>\n\n"
    text += "\n".join(f"• {c['title']}" for c in channels) if channels else "Hozircha kanal yo'q."
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb_admin_channels(channels))


async def on_add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    count = await db.count_global_channels()
    if count >= config.MAX_GLOBAL_MANDATORY_CHANNELS:
        await query.answer("❌ Maksimal limitga yetdingiz!", show_alert=True)
        return
    await query.answer()
    await query.edit_message_text(
        f"➕ Kanaldan xabarni forward qiling (bot o'sha kanalda admin bo'lishi shart).\n"
        f"Bekor qilish uchun /cancel",
        reply_markup=kb_back("adm_channels"),
    )
    return WAIT_ADD_CHANNEL


async def on_add_channel_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    chat = await get_chat_from_forward(msg)
    if chat is None:
        await msg.reply_text("❌ Bu forward emas. Kanaldan xabarni forward qiling.")
        return WAIT_ADD_CHANNEL
    if not await is_bot_admin_in_chat(context, chat.id):
        await msg.reply_text(texts.CHAT_NOT_ADMIN, parse_mode="HTML")
        return WAIT_ADD_CHANNEL
    count = await db.count_global_channels()
    if count >= config.MAX_GLOBAL_MANDATORY_CHANNELS:
        await msg.reply_text("❌ Maksimal limitga yetdingiz!")
        return ConversationHandler.END
    link = await get_chat_invite_link(context, chat)
    await db.add_global_channel(chat.id, chat.title or str(chat.id), link, update.effective_user.id)
    await msg.reply_text(f"✅ Global majburiy kanal qo'shildi: {chat.title}")
    await msg.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())
    return ConversationHandler.END


# ══════════════════════════════════════════════════════
# FOYDALANUVCHILAR
# ══════════════════════════════════════════════════════
async def on_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    total = await db.count_users()
    await query.edit_message_text(
        f"👥 <b>Foydalanuvchilar</b>\n\nJami: {total} ta\n\nKerakli amalni tanlang:",
        parse_mode="HTML",
        reply_markup=kb_admin_users(),
    )


def _make_id_waiter(prompt: str, next_state: int):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(prompt, reply_markup=kb_back("adm_users"))
        return next_state
    return handler


on_ban_start = _make_id_waiter("🚫 Ban qilinadigan foydalanuvchi ID sini yuboring:", WAIT_BAN_ID)
on_unban_start = _make_id_waiter("✅ Unban qilinadigan foydalanuvchi ID sini yuboring:", WAIT_UNBAN_ID)
on_warn_start = _make_id_waiter("⚠️ Ogohlantirish beriladigan foydalanuvchi ID sini yuboring:", WAIT_WARN_ID)
on_info_start = _make_id_waiter("👤 Ma'lumot olinadigan foydalanuvchi ID sini yuboring:", WAIT_INFO_ID)


async def on_ban_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.strip().isdigit():
        await update.message.reply_text("❌ Faqat raqam (ID) yuboring.")
        return WAIT_BAN_ID
    uid = int(update.message.text.strip())
    await db.set_ban(uid, True)
    await update.message.reply_text(f"🚫 {uid} bloklandi.")
    await update.message.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())
    return ConversationHandler.END


async def on_unban_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.strip().isdigit():
        await update.message.reply_text("❌ Faqat raqam (ID) yuboring.")
        return WAIT_UNBAN_ID
    uid = int(update.message.text.strip())
    await db.set_ban(uid, False)
    await update.message.reply_text(f"✅ {uid} blokdan chiqarildi.")
    await update.message.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())
    return ConversationHandler.END


async def on_warn_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.strip().isdigit():
        await update.message.reply_text("❌ Faqat raqam (ID) yuboring.")
        return WAIT_WARN_ID
    uid = int(update.message.text.strip())
    count = await db.add_warning(uid)
    await update.message.reply_text(f"⚠️ {uid} ga ogohlantirish berildi. Jami: {count}")
    try:
        await context.bot.send_message(uid, "⚠️ Sizga admin tomonidan ogohlantirish berildi.")
    except Exception:
        pass
    await update.message.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())
    return ConversationHandler.END


async def on_info_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.strip().isdigit():
        await update.message.reply_text("❌ Faqat raqam (ID) yuboring.")
        return WAIT_INFO_ID
    uid = int(update.message.text.strip())
    u = await db.get_user(uid)
    if not u:
        await update.message.reply_text("❌ Foydalanuvchi topilmadi.")
        return ConversationHandler.END
    is_pro = await db.is_pro(uid)
    contests = await db.contests_by_owner(uid)
    banned_str = "Ha" if u["is_banned"] else "Yo'q"
    pro_str = "✅ Ha" if is_pro else "❌ Yo'q"
    text = (
        f"👤 <b>Foydalanuvchi ma'lumoti</b>\n\n"
        f"ID: {u['user_id']}\n"
        f"Username: @{u['username'] or '—'}\n"
        f"Ism: {u['first_name']}\n"
        f"Bloklangan: {banned_str}\n"
        f"Ogohlantirishlar: {u['warnings']}\n"
        f"PRO: {pro_str}\n"
        f"Konkurslari: {len(contests)} ta\n"
    )
    await update.message.reply_text(text, parse_mode="HTML")
    await update.message.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())
    return ConversationHandler.END


async def on_top_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    top = await db.top_users(10)
    lines = []
    for i, u in enumerate(top, 1):
        uname = f"@{u['username']}" if u["username"] else f"ID:{u['user_id']}"
        lines.append(f"{i}. {uname} — {u['joined']} ta qatnashgan, {u['won']} ta g'olib")
    text = "🏆 <b>TOP foydalanuvchilar</b>\n\n" + ("\n".join(lines) if lines else "Ma'lumot yo'q.")
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb_back("adm_users"))


# ══════════════════════════════════════════════════════
# BARCHA KONKURSLAR / STATISTIKA
# ══════════════════════════════════════════════════════
async def on_contests_overview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    active = await db.active_contests()
    total = await db.count_contests()
    lines = [f"🆔 #{c['id']} — {c['chat_title']} (owner:{c['owner_id']})" for c in active[:20]]
    text = (
        f"🔥 <b>Konkurslar</b>\n\nJami: {total} ta\nFaol: {len(active)} ta\n\n"
        + ("\n".join(lines) if lines else "Faol konkurs yo'q.")
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb_back("adm_back"))


async def on_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    users = await db.count_users()
    pro_users = await db.count_pro_users()
    contests = await db.count_contests()
    active = len(await db.active_contests())
    global_ch = await db.count_global_channels()
    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"💎 PRO foydalanuvchilar: {pro_users}\n"
        f"🎉 Jami konkurslar: {contests}\n"
        f"🟢 Faol konkurslar: {active}\n"
        f"🌍 Global kanallar: {global_ch}\n"
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb_back("adm_back"))


# ══════════════════════════════════════════════════════
# BROADCAST
# ══════════════════════════════════════════════════════
async def on_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting (matn):",
        reply_markup=kb_back("adm_back"),
    )
    return WAIT_BROADCAST


async def on_broadcast_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    ids = await db.all_user_ids()
    sent, failed = 0, 0
    status_msg = await update.message.reply_text(f"📤 Yuborilmoqda... 0/{len(ids)}")
    for i, uid in enumerate(ids, 1):
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        if i % 25 == 0:
            try:
                await status_msg.edit_text(f"📤 Yuborilmoqda... {i}/{len(ids)}")
            except Exception:
                pass
    await status_msg.edit_text(f"✅ Yuborildi: {sent} ta\n❌ Xato: {failed} ta")
    await update.message.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())
    return ConversationHandler.END


# ══════════════════════════════════════════════════════
# PRO BOSHQARUVI (admin tomonidan qo'lda berish)
# ══════════════════════════════════════════════════════
async def on_pro_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pro_count = await db.count_pro_users()
    await query.edit_message_text(
        f"💎 <b>PRO boshqaruvi</b>\n\nHozirda PRO: {pro_count} ta foydalanuvchi\n\n"
        f"Foydalanuvchilarga qo'lda PRO berish yoki olib tashlash mumkin:",
        parse_mode="HTML",
        reply_markup=kb_admin_pro(),
    )


async def on_grant_pro_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ Format: <code>USER_ID KUNLAR</code>\nMasalan: <code>123456789 30</code>",
        parse_mode="HTML",
        reply_markup=kb_back("adm_pro"),
    )
    return WAIT_GRANT_PRO


async def on_grant_pro_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) != 2 or not all(p.lstrip("-").isdigit() for p in parts):
        await update.message.reply_text("❌ Format: USER_ID KUNLAR")
        return WAIT_GRANT_PRO
    uid, days = int(parts[0]), int(parts[1])
    until = await db.set_pro(uid, days)
    await update.message.reply_text(
        f"✅ {uid} foydalanuvchiga {days} kunlik PRO berildi.\n"
        f"Tugash: {time.strftime('%d.%m.%Y %H:%M', time.localtime(until))}"
    )
    try:
        await context.bot.send_message(uid, texts.PRO_PURCHASED.format(days=days), parse_mode="HTML")
    except Exception:
        pass
    await update.message.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())
    return ConversationHandler.END


async def on_revoke_pro_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("➖ PRO olib tashlanadigan USER_ID ni yuboring:", reply_markup=kb_back("adm_pro"))
    return WAIT_REVOKE_PRO


async def on_revoke_pro_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.strip().isdigit():
        await update.message.reply_text("❌ Faqat raqam (ID) yuboring.")
        return WAIT_REVOKE_PRO
    uid = int(update.message.text.strip())
    await db.revoke_pro(uid)
    await update.message.reply_text(f"✅ {uid} dan PRO olib tashlandi.")
    await update.message.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())
    return ConversationHandler.END


async def on_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(texts.ADMIN_MAIN, parse_mode="HTML", reply_markup=kb_admin_main())
    return ConversationHandler.END


def register(app: Application):
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(MessageHandler(filters.Regex("^🔧 Admin Panel$"), cmd_admin))

    app.add_handler(CallbackQueryHandler(on_admin_back, pattern="^adm_back$"))
    app.add_handler(CallbackQueryHandler(on_channels_menu, pattern="^adm_channels$"))
    app.add_handler(CallbackQueryHandler(on_delete_channel, pattern="^adm_delch_"))
    app.add_handler(CallbackQueryHandler(on_users_menu, pattern="^adm_users$"))
    app.add_handler(CallbackQueryHandler(on_top_users, pattern="^adm_top$"))
    app.add_handler(CallbackQueryHandler(on_contests_overview, pattern="^adm_contests$"))
    app.add_handler(CallbackQueryHandler(on_stats, pattern="^adm_stats$"))
    app.add_handler(CallbackQueryHandler(on_pro_menu, pattern="^adm_pro$"))

    admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(on_add_channel_start, pattern="^adm_addch$"),
            CallbackQueryHandler(on_ban_start, pattern="^adm_ban$"),
            CallbackQueryHandler(on_unban_start, pattern="^adm_unban$"),
            CallbackQueryHandler(on_warn_start, pattern="^adm_warn$"),
            CallbackQueryHandler(on_info_start, pattern="^adm_info$"),
            CallbackQueryHandler(on_broadcast_start, pattern="^adm_broadcast$"),
            CallbackQueryHandler(on_grant_pro_start, pattern="^adm_grantpro$"),
            CallbackQueryHandler(on_revoke_pro_start, pattern="^adm_revokepro$"),
        ],
        states={
            WAIT_ADD_CHANNEL: [MessageHandler(filters.FORWARDED & ~filters.COMMAND, on_add_channel_receive)],
            WAIT_BAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_ban_id)],
            WAIT_UNBAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_unban_id)],
            WAIT_WARN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_warn_id)],
            WAIT_INFO_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_info_id)],
            WAIT_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_broadcast_receive)],
            WAIT_GRANT_PRO: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_grant_pro_receive)],
            WAIT_REVOKE_PRO: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_revoke_pro_receive)],
        },
        fallbacks=[CommandHandler("cancel", on_cancel)],
        name="admin_panel_conv",
        persistent=False,
    )
    app.add_handler(admin_conv)
