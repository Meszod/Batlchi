# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 KONKURS YARATISH SIZARDI
 Har qanday foydalanuvchi "+ Konkurs qilish" tugmasi orqali
 o'z kanal/guruhida konkurs o'tkaza oladi.
 5 xil tur: 🗳 Ovoz to'plash / ⭐ Stars Battle / 👥 Referal /
 🎲 Oddiy Random / 📸 Rasm-Video.
 Tugash sharti: vaqt / ishtirokchilar soni / ikkalasi ham.
 Joylash: hozir yoki rejalashtirilgan vaqtda.
══════════════════════════════════════════════════════════
"""
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application, ConversationHandler, MessageHandler, CallbackQueryHandler,
    CommandHandler, ContextTypes, filters,
)

import config
import texts
from database import db
from keyboards import (
    kb_cancel, kb_type_select, kb_sponsor_step, kb_boost_step, kb_duration,
    kb_winners_count, kb_confirm, kb_join_button, kb_end_condition,
    kb_target_count, kb_publish_timing, kb_schedule_presets,
)
from utils import (
    get_chat_from_forward, is_bot_admin_in_chat, is_user_admin_in_chat,
    get_chat_invite_link, format_duration,
)
from handlers.contest_join import schedule_contest_monitor, schedule_contest_publish, build_post_text

logger = logging.getLogger(__name__)

(ASK_TYPE, ASK_CHAT, ASK_SPONSOR, ASK_BOOST, ASK_END_CONDITION, ASK_DURATION,
 ASK_DURATION_CUSTOM, ASK_TARGET_COUNT, ASK_TARGET_COUNT_CUSTOM, ASK_WINNERS,
 ASK_PUBLISH_TIMING, ASK_SCHEDULE_TIME, CONFIRM) = range(13)


def _reset_wizard(context: ContextTypes.DEFAULT_TYPE):
    context.user_data["wizard"] = {
        "type": "stars",
        "chat_id": None,
        "chat_title": None,
        "chat_link": None,
        "sponsors": [],
        "boost_chat_id": None,
        "boost_link": None,
        "require_boost": False,
        "end_condition": "time",
        "duration_minutes": None,
        "target_participants": None,
        "winners_count": 1,
        "publish_at": None,  # None = hozir joylash
    }


async def entry_create_contest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if await db.is_banned(user.id):
        await update.message.reply_text("🚫 Siz bloklangansiz.")
        return ConversationHandler.END
    _reset_wizard(context)
    await update.message.reply_text(
        texts.ASK_TYPE.format(
            stars_points=config.STARS_VOTE_POINTS,
            reaction_points=config.REACTION_POINTS,
            boost_points=config.BOOST_POINTS,
            referral_points=config.REFERRAL_POINTS,
        ),
        parse_mode="HTML",
        reply_markup=kb_type_select(),
    )
    return ASK_TYPE


async def on_type_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ctype = query.data.split("_", 1)[1]
    context.user_data["wizard"]["type"] = ctype
    await query.edit_message_text(texts.ASK_CHAT, parse_mode="HTML", reply_markup=kb_cancel())
    return ASK_CHAT


async def on_chat_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message
    chat = await get_chat_from_forward(msg)
    if chat is None:
        await msg.reply_text(
            "❌ Bu forward emas. Iltimos kanal/guruhdan xabarni forward qiling.",
            reply_markup=kb_cancel(),
        )
        return ASK_CHAT

    if not await is_bot_admin_in_chat(context, chat.id):
        await msg.reply_text(texts.CHAT_NOT_ADMIN, parse_mode="HTML", reply_markup=kb_cancel())
        return ASK_CHAT

    if not await is_user_admin_in_chat(context, chat.id, update.effective_user.id):
        await msg.reply_text(texts.USER_NOT_CHAT_ADMIN, parse_mode="HTML", reply_markup=kb_cancel())
        return ASK_CHAT

    link = await get_chat_invite_link(context, chat)
    w = context.user_data["wizard"]
    w["chat_id"] = chat.id
    w["chat_title"] = chat.title or chat.full_name or str(chat.id)
    w["chat_link"] = link

    await msg.reply_text(
        texts.CHAT_CONFIRMED.format(
            title=w["chat_title"], max_n=config.MAX_SPONSOR_CHANNELS_PER_CONTEST
        ),
        parse_mode="HTML",
        reply_markup=kb_sponsor_step(),
    )
    return ASK_SPONSOR


async def on_sponsor_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message
    w = context.user_data["wizard"]
    if len(w["sponsors"]) >= config.MAX_SPONSOR_CHANNELS_PER_CONTEST:
        await msg.reply_text(
            f"⚠️ Maksimal {config.MAX_SPONSOR_CHANNELS_PER_CONTEST} ta homiy kanal qo'shildi.",
            reply_markup=kb_sponsor_step(),
        )
        return ASK_SPONSOR

    chat = await get_chat_from_forward(msg)
    if chat is None:
        await msg.reply_text(
            "❌ Bu forward emas. Kanaldan xabar forward qiling yoki ✅ Tayyor tugmasini bosing.",
            reply_markup=kb_sponsor_step(),
        )
        return ASK_SPONSOR

    if not await is_bot_admin_in_chat(context, chat.id):
        await msg.reply_text(texts.SPONSOR_NOT_ADMIN, reply_markup=kb_sponsor_step())
        return ASK_SPONSOR

    link = await get_chat_invite_link(context, chat)
    title = chat.title or str(chat.id)
    w["sponsors"].append({"chat_id": chat.id, "title": title, "link": link})

    await msg.reply_text(
        texts.SPONSOR_ADDED.format(title=title), parse_mode="HTML", reply_markup=kb_sponsor_step()
    )
    return ASK_SPONSOR


async def on_sponsor_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    w = context.user_data["wizard"]

    if w["type"] != "stars":
        await query.edit_message_text(texts.ASK_END_CONDITION, parse_mode="HTML", reply_markup=kb_end_condition())
        return ASK_END_CONDITION

    await query.edit_message_text(
        texts.ASK_BOOST.format(points=config.BOOST_POINTS), parse_mode="HTML", reply_markup=kb_boost_step()
    )
    return ASK_BOOST


async def on_boost_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message
    chat = await get_chat_from_forward(msg)
    if chat is None:
        await msg.reply_text(
            "❌ Bu forward emas. Kanaldan xabar forward qiling yoki ❌ Kerak emas tugmasini bosing.",
            reply_markup=kb_boost_step(),
        )
        return ASK_BOOST

    w = context.user_data["wizard"]
    username = getattr(chat, "username", None)
    if not username:
        await msg.reply_text(
            "❌ Boost havolasi faqat public (username'li) kanallar uchun ishlaydi.",
            reply_markup=kb_boost_step(),
        )
        return ASK_BOOST

    w["boost_chat_id"] = chat.id
    w["boost_link"] = f"https://t.me/boost/{username}"
    w["require_boost"] = True

    await msg.reply_text(
        texts.BOOST_SET.format(title=chat.title or username, points=config.BOOST_POINTS), parse_mode="HTML"
    )
    await msg.reply_text(texts.ASK_END_CONDITION, parse_mode="HTML", reply_markup=kb_end_condition())
    return ASK_END_CONDITION


async def on_boost_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(texts.ASK_END_CONDITION, parse_mode="HTML", reply_markup=kb_end_condition())
    return ASK_END_CONDITION


# ══════════════════════════════════════════════════════
# 🏁 TUGASH SHARTI: vaqt / ishtirokchilar soni / ikkalasi
# ══════════════════════════════════════════════════════
async def on_end_condition_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data.split("_", 1)[1]  # 'time' | 'count' | 'both'
    context.user_data["wizard"]["end_condition"] = choice

    if choice == "count":
        await query.edit_message_text(texts.ASK_TARGET_COUNT, parse_mode="HTML", reply_markup=kb_target_count())
        return ASK_TARGET_COUNT

    is_pro = await db.is_pro(update.effective_user.id)
    await query.edit_message_text(
        texts.ASK_DURATION.format(pro_days=config.PRO_MAX_DURATION_MINUTES // 1440),
        parse_mode="HTML",
        reply_markup=kb_duration(is_pro),
    )
    return ASK_DURATION


async def on_duration_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cb = query.data

    if cb == "dur_custom":
        await query.edit_message_text(
            "✏️ Davomiylikni daqiqada kiriting (masalan: 90):", reply_markup=kb_cancel()
        )
        return ASK_DURATION_CUSTOM

    minutes = int(cb.split("_")[1])
    return await _apply_duration(update, context, minutes, via_callback=True)


async def on_duration_custom_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip()
    if not txt.isdigit() or int(txt) <= 0:
        await update.message.reply_text("❌ Faqat musbat butun son kiriting (daqiqada).", reply_markup=kb_cancel())
        return ASK_DURATION_CUSTOM
    return await _apply_duration(update, context, int(txt), via_callback=False)


async def _apply_duration(update: Update, context: ContextTypes.DEFAULT_TYPE, minutes: int, via_callback: bool) -> int:
    user_id = update.effective_user.id
    is_pro = await db.is_pro(user_id)
    max_allowed = config.PRO_MAX_DURATION_MINUTES if is_pro else config.FREE_MAX_DURATION_MINUTES

    if minutes > max_allowed:
        text = texts.DURATION_TOO_LONG_FREE if not is_pro else (
            f"❌ Maksimal ruxsat etilgan davomiylik: {format_duration(max_allowed)}."
        )
        if via_callback:
            await update.callback_query.edit_message_text(
                text, parse_mode="HTML", reply_markup=kb_duration(is_pro)
            )
        else:
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb_cancel())
        return ASK_DURATION

    w = context.user_data["wizard"]
    w["duration_minutes"] = minutes

    # 'both' tanlangan bo'lsa — endi ishtirokchilar sonini ham so'raymiz
    if w["end_condition"] == "both":
        if via_callback:
            await update.callback_query.edit_message_text(
                texts.ASK_TARGET_COUNT, parse_mode="HTML", reply_markup=kb_target_count()
            )
        else:
            await update.message.reply_text(
                texts.ASK_TARGET_COUNT, parse_mode="HTML", reply_markup=kb_target_count()
            )
        return ASK_TARGET_COUNT

    if via_callback:
        await update.callback_query.edit_message_text(
            texts.ASK_WINNERS_COUNT, parse_mode="HTML", reply_markup=kb_winners_count()
        )
    else:
        await update.message.reply_text(
            texts.ASK_WINNERS_COUNT, parse_mode="HTML", reply_markup=kb_winners_count()
        )
    return ASK_WINNERS


# ══════════════════════════════════════════════════════
# 👥 ISHTIROKCHILAR SONI (tugash sharti sifatida)
# ══════════════════════════════════════════════════════
async def on_target_count_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cb = query.data

    if cb == "tcount_custom":
        await query.edit_message_text(
            "✏️ Ishtirokchilar sonini kiriting (masalan: 75):", reply_markup=kb_cancel()
        )
        return ASK_TARGET_COUNT_CUSTOM

    n = int(cb.split("_")[1])
    return await _apply_target_count(update, context, n, via_callback=True)


async def on_target_count_custom_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip()
    if not txt.isdigit() or int(txt) <= 0:
        await update.message.reply_text(texts.TARGET_COUNT_INVALID, reply_markup=kb_cancel())
        return ASK_TARGET_COUNT_CUSTOM
    return await _apply_target_count(update, context, int(txt), via_callback=False)


async def _apply_target_count(update: Update, context: ContextTypes.DEFAULT_TYPE, n: int, via_callback: bool) -> int:
    context.user_data["wizard"]["target_participants"] = n
    if via_callback:
        await update.callback_query.edit_message_text(
            texts.ASK_WINNERS_COUNT, parse_mode="HTML", reply_markup=kb_winners_count()
        )
    else:
        await update.message.reply_text(
            texts.ASK_WINNERS_COUNT, parse_mode="HTML", reply_markup=kb_winners_count()
        )
    return ASK_WINNERS


async def on_winners_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    n = int(query.data.split("_")[1])
    context.user_data["wizard"]["winners_count"] = n
    await query.edit_message_text(texts.ASK_PUBLISH_TIMING, parse_mode="HTML", reply_markup=kb_publish_timing())
    return ASK_PUBLISH_TIMING


# ══════════════════════════════════════════════════════
# 📅 JOYLASH VAQTI: hozir / rejalashtirish
# ══════════════════════════════════════════════════════
async def on_publish_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["wizard"]["publish_at"] = None
    return await _show_confirm_summary(update, context, via_callback=True)


async def on_publish_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(texts.ASK_SCHEDULE_TIME, parse_mode="HTML", reply_markup=kb_schedule_presets())
    return ASK_SCHEDULE_TIME


async def on_schedule_preset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    minutes = int(query.data.split("_")[1])
    publish_at = datetime.now().timestamp() + minutes * 60
    context.user_data["wizard"]["publish_at"] = publish_at
    return await _show_confirm_summary(update, context, via_callback=True)


async def on_schedule_custom_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Sana-vaqtni kiriting: <code>05.09.2026 18:00</code> ko'rinishida",
        parse_mode="HTML", reply_markup=kb_cancel(),
    )
    return ASK_SCHEDULE_TIME


async def on_schedule_custom_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip()
    try:
        dt = datetime.strptime(txt, "%d.%m.%Y %H:%M")
    except ValueError:
        await update.message.reply_text(texts.SCHEDULE_TIME_INVALID, parse_mode="HTML", reply_markup=kb_cancel())
        return ASK_SCHEDULE_TIME

    if dt <= datetime.now():
        await update.message.reply_text(texts.SCHEDULE_TIME_INVALID, parse_mode="HTML", reply_markup=kb_cancel())
        return ASK_SCHEDULE_TIME

    context.user_data["wizard"]["publish_at"] = dt.timestamp()
    return await _show_confirm_summary(update, context, via_callback=False)


def _format_end_info(w: dict) -> str:
    if w["end_condition"] == "time":
        return format_duration(w["duration_minutes"])
    if w["end_condition"] == "count":
        return f"{w['target_participants']} kishi bo'lganda"
    return f"{format_duration(w['duration_minutes'])} YOKI {w['target_participants']} kishi (birinchi bo'lgani)"


def _format_publish_info(w: dict) -> str:
    if not w["publish_at"]:
        return "Hozir"
    dt = datetime.fromtimestamp(w["publish_at"])
    return dt.strftime("%d.%m.%Y %H:%M")


async def _show_confirm_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, via_callback: bool) -> int:
    user_id = update.effective_user.id
    w = context.user_data["wizard"]
    is_pro = await db.is_pro(user_id)
    use_global = not is_pro
    global_count = await db.count_global_channels() if use_global else 0
    sponsors_str = ", ".join(s["title"] for s in w["sponsors"]) if w["sponsors"] else "yo'q"
    global_ch_str = (
        f"{global_count} ta (majburiy)" if use_global and global_count else
        ("PRO tufayli yo'q 💎" if is_pro else "yo'q")
    )
    end_info = _format_end_info(w)
    publish_info = _format_publish_info(w)

    _SUMMARY_TEMPLATES = {
        "vote": texts.CONFIRM_SUMMARY_VOTE,
        "referral": texts.CONFIRM_SUMMARY_REFERRAL,
        "random": texts.CONFIRM_SUMMARY_RANDOM,
        "media": texts.CONFIRM_SUMMARY_MEDIA,
    }

    if w["type"] in _SUMMARY_TEMPLATES:
        summary = _SUMMARY_TEMPLATES[w["type"]].format(
            title=w["chat_title"], sponsors=sponsors_str,
            end_info=end_info, publish_info=publish_info,
            winners=w["winners_count"], global_ch=global_ch_str,
        )
    else:  # stars
        boost_str = (
            f"✅ yoqilgan, +{config.BOOST_POINTS} ball ({w['boost_link']})"
            if w["require_boost"] else "❌ yo'q"
        )
        summary = texts.CONFIRM_SUMMARY_STARS.format(
            title=w["chat_title"], sponsors=sponsors_str, boost=boost_str,
            end_info=end_info, publish_info=publish_info,
            winners=w["winners_count"], global_ch=global_ch_str,
        )

    if via_callback:
        await update.callback_query.edit_message_text(summary, parse_mode="HTML", reply_markup=kb_confirm())
    else:
        await update.message.reply_text(summary, parse_mode="HTML", reply_markup=kb_confirm())
    return CONFIRM


async def on_confirm_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    w = context.user_data.get("wizard")
    if not w or not w.get("chat_id"):
        await query.edit_message_text(texts.CONTEST_CANCELLED)
        return ConversationHandler.END

    is_pro = await db.is_pro(user.id)
    now = datetime.now().timestamp()

    # end_time faqat 'time'/'both' rejimida hisoblanadi; 'count' bo'lsa ham
    # cheksiz osilib qolmasligi uchun yashirin xavfsizlik chegarasi qo'yiladi
    max_allowed = config.PRO_MAX_DURATION_MINUTES if is_pro else config.FREE_MAX_DURATION_MINUTES
    if w["end_condition"] in ("time", "both"):
        duration_for_end = w["duration_minutes"]
    else:
        duration_for_end = max_allowed  # faqat xavfsizlik zaxirasi, foydalanuvchiga ko'rsatilmaydi

    is_scheduled = bool(w["publish_at"])
    status = "scheduled" if is_scheduled else "active"
    start_time = None if is_scheduled else now
    end_time = None if is_scheduled else now + duration_for_end * 60

    contest_id = await db.create_contest(
        owner_id=user.id,
        type=w["type"],
        chat_id=w["chat_id"],
        chat_title=w["chat_title"],
        chat_link=w["chat_link"],
        message_id=0,
        sponsor_channels=w["sponsors"],
        boost_chat_id=w["boost_chat_id"],
        boost_link=w["boost_link"],
        require_boost=int(w["require_boost"]),
        use_global_channels=int(not is_pro),
        winners_count=w["winners_count"],
        duration_minutes=duration_for_end,
        end_condition=w["end_condition"],
        target_participants=w["target_participants"],
        publish_at=w["publish_at"],
        start_time=start_time,
        end_time=end_time,
        status=status,
    )

    if is_scheduled:
        schedule_contest_publish(context.application, contest_id, w["publish_at"])
        await query.edit_message_text(
            texts.CONTEST_SCHEDULED_OWNER.format(
                title=w["chat_title"], when=_format_publish_info(w)
            ),
            parse_mode="HTML",
        )
        context.user_data.pop("wizard", None)
        return ConversationHandler.END

    # Kanalga / guruhga post joylash (turi bo'yicha shablon avtomatik tanlanadi)
    contest = await db.get_contest(contest_id)
    contest["_required_channels"] = w["sponsors"] or (not is_pro)
    post_text = build_post_text(contest, count=0)
    try:
        sent = await context.bot.send_message(
            w["chat_id"], post_text, parse_mode="HTML",
            reply_markup=kb_join_button(contest_id, w["type"], bool(w["require_boost"])),
        )
        await db.update_contest(contest_id, message_id=sent.message_id)
    except Exception as e:
        logger.error(f"Konkurs postini joylashda xato: {e}")
        await query.edit_message_text(
            "⚠️ Konkurs yaratildi, lekin kanalga post joylashda xatolik yuz berdi. "
            "Botga kanalda xabar yuborish huquqi berilganini tekshiring."
        )
        return ConversationHandler.END

    schedule_contest_monitor(context.application, contest_id)

    await query.edit_message_text(
        texts.CONTEST_STARTED_OWNER.format(
            title=w["chat_title"], duration=_format_end_info(w)
        ),
        parse_mode="HTML",
    )
    context.user_data.pop("wizard", None)
    return ConversationHandler.END


async def on_wizard_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(texts.CONTEST_CANCELLED)
    context.user_data.pop("wizard", None)
    return ConversationHandler.END


async def on_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("wizard", None)
    await update.message.reply_text(texts.CONTEST_CANCELLED)
    return ConversationHandler.END


def register(app: Application):
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Konkurs qilish$"), entry_create_contest)],
        states={
            ASK_TYPE: [
                CallbackQueryHandler(on_type_choice, pattern="^ctype_"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
            ],
            ASK_CHAT: [
                MessageHandler(filters.FORWARDED & ~filters.COMMAND, on_chat_forward),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
            ],
            ASK_SPONSOR: [
                CallbackQueryHandler(on_sponsor_done, pattern="^sponsor_done$"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
                MessageHandler(filters.FORWARDED & ~filters.COMMAND, on_sponsor_forward),
            ],
            ASK_BOOST: [
                CallbackQueryHandler(on_boost_skip, pattern="^boost_skip$"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
                MessageHandler(filters.FORWARDED & ~filters.COMMAND, on_boost_forward),
            ],
            ASK_END_CONDITION: [
                CallbackQueryHandler(on_end_condition_choice, pattern="^endc_"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
            ],
            ASK_DURATION: [
                CallbackQueryHandler(on_duration_choice, pattern="^dur_"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
            ],
            ASK_DURATION_CUSTOM: [
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, on_duration_custom_text),
            ],
            ASK_TARGET_COUNT: [
                CallbackQueryHandler(on_target_count_choice, pattern="^tcount_"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
            ],
            ASK_TARGET_COUNT_CUSTOM: [
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, on_target_count_custom_text),
            ],
            ASK_WINNERS: [
                CallbackQueryHandler(on_winners_choice, pattern="^win_"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
            ],
            ASK_PUBLISH_TIMING: [
                CallbackQueryHandler(on_publish_now, pattern="^pub_now$"),
                CallbackQueryHandler(on_publish_schedule, pattern="^pub_schedule$"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
            ],
            ASK_SCHEDULE_TIME: [
                CallbackQueryHandler(on_schedule_preset, pattern="^sched_\\d+$"),
                CallbackQueryHandler(on_schedule_custom_prompt, pattern="^sched_custom$"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, on_schedule_custom_text),
            ],
            CONFIRM: [
                CallbackQueryHandler(on_confirm_start, pattern="^confirm_start$"),
                CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", on_cancel_command),
            CallbackQueryHandler(on_wizard_cancel, pattern="^wizard_cancel$"),
        ],
        name="contest_create_wizard",
        persistent=False,
    )
    app.add_handler(conv)
