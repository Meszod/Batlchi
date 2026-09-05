# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 KONKURSGA QO'SHILISH + BALL TIZIMI + MONITORING
 - Qo'shilish uchun faqat majburiy kanallarga obuna kifoya.
 - Boost — ixtiyoriy bonus: +BOOST_POINTS ball beradi (majburiy EMAS).
 - G'oliblar konkurs tugaganda BALL REYTINGI bo'yicha avtomatik aniqlanadi.
══════════════════════════════════════════════════════════
"""
import logging
import time

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, MessageReactionHandler, ContextTypes

import config
import texts
from database import db
from keyboards import kb_join_button, kb_missing_channels
from utils import (
    check_user_membership, check_user_boosted, gather_required_channels, format_remaining, format_dt,
)

logger = logging.getLogger(__name__)


async def _finalize_join(context: ContextTypes.DEFAULT_TYPE, contest: dict, contest_id: int, user):
    """Barcha majburiy kanallarga a'zolik tasdiqlangandan keyingi qo'shilish logikasi."""
    await db.add_participant(contest_id, user.id)
    await db.upsert_user(user.id, user.username or "", user.first_name or "")

    # 👥 Referal orqali kelgan bo'lsa — taklif qilganga ball beramiz
    # (DB'dan o'qiymiz — bot qayta ishga tushgan bo'lsa ham yo'qolmaydi)
    pending = await db.pop_pending_referral(user.id)
    if pending and pending.get("contest_id") == contest_id and contest.get("type") == "referral":
        credited = await db.register_referral(contest_id, user.id, pending["referrer_id"])
        if credited:
            try:
                await context.bot.send_message(
                    pending["referrer_id"],
                    texts.REFERRAL_CREDITED.format(points=config.REFERRAL_POINTS),
                )
            except Exception:
                pass

    # 📸 Rasm/Video turi — qo'shilgach darhol ish yuborishni so'raymiz (DM orqali)
    if contest.get("type") == "media":
        context.user_data["awaiting_media_contest"] = contest_id
        try:
            await context.bot.send_message(user.id, texts.MEDIA_ASK_SUBMISSION, parse_mode="HTML")
        except Exception:
            pass

    await _refresh_post(context, contest_id)

    # 👥 Ishtirokchilar soni bo'yicha tugash sharti — darhol tekshiramiz
    if contest.get("end_condition") in ("count", "both") and contest.get("target_participants"):
        current_count = await db.count_participants(contest_id)
        if current_count >= contest["target_participants"]:
            await draw_and_announce_winners(context, contest_id, reason="ishtirokchilar soni to'ldi")


async def on_join_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    contest_id = int(query.data.split("_")[1])

    if await db.is_banned(user.id):
        await query.answer(texts.JOIN_BANNED, show_alert=True)
        return

    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active":
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return

    if await db.is_participant(contest_id, user.id):
        await query.answer(texts.JOIN_ALREADY, show_alert=True)
        return

    # ── faqat majburiy kanallar tekshiriladi (boost EMAS — u ixtiyoriy bonus) ──
    required = await gather_required_channels(db, contest)
    missing = []
    for ch in required:
        ok = await check_user_membership(context, ch["chat_id"], user.id)
        if not ok:
            missing.append(ch)

    if missing:
        # Native alert matn-only bo'lgani uchun (link bosilmaydi) — havolalarni
        # foydalanuvchiga shaxsiy xabar (DM) orqali, tugma ko'rinishida yuboramiz.
        try:
            await context.bot.send_message(
                user.id, texts.JOIN_MISSING_DM_HEADER, parse_mode="HTML",
                reply_markup=kb_missing_channels(contest_id, missing),
            )
            await query.answer(texts.JOIN_MISSING_SENT_DM, show_alert=True)
        except Exception:
            # DM yozib bo'lmadi (foydalanuvchi botni ishga tushirmagan) —
            # pastdagi "🤖 Botni ishga tushirish" tugmasidan foydalanishini so'raymiz.
            me = await context.bot.get_me()
            await query.answer(
                f"❌ Avval pastdagi \"🤖 Botni ishga tushirish\" tugmasini bosing, "
                f"so'ng qaytadan urinib ko'ring.",
                show_alert=True,
            )
        return

    await _finalize_join(context, contest, contest_id, user)
    await query.answer(texts.JOIN_SUCCESS, show_alert=True)


async def on_join_recheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DM'dagi '✅ Tekshirish' tugmasi — kanallarga a'zolikni qayta tekshiradi."""
    query = update.callback_query
    user = update.effective_user
    contest_id = int(query.data.split("_")[1])

    if await db.is_banned(user.id):
        await query.answer(texts.JOIN_BANNED, show_alert=True)
        return

    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active":
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return

    if await db.is_participant(contest_id, user.id):
        await query.answer(texts.JOIN_ALREADY, show_alert=True)
        try:
            await query.edit_message_text(texts.JOIN_ALREADY)
        except Exception:
            pass
        return

    required = await gather_required_channels(db, contest)
    missing = []
    for ch in required:
        ok = await check_user_membership(context, ch["chat_id"], user.id)
        if not ok:
            missing.append(ch)

    if missing:
        await query.answer(texts.JOIN_RECHECK_STILL_MISSING, show_alert=True)
        try:
            await query.edit_message_reply_markup(reply_markup=kb_missing_channels(contest_id, missing))
        except Exception:
            pass
        return

    await _finalize_join(context, contest, contest_id, user)
    await query.answer(texts.JOIN_RECHECK_SUCCESS, show_alert=True)
    try:
        await query.edit_message_text(texts.JOIN_RECHECK_SUCCESS)
    except Exception:
        pass


async def on_boost_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ixtiyoriy boost bonusi — majburiy EMAS, faqat +ball beradi."""
    query = update.callback_query
    user = update.effective_user
    contest_id = int(query.data.split("_")[1])

    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active":
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return

    if not await db.is_participant(contest_id, user.id):
        await query.answer(texts.BOOST_NOT_JOINED, show_alert=True)
        return

    if await db.is_boosted(contest_id, user.id):
        await query.answer(texts.BOOST_ALREADY, show_alert=True)
        return

    if not contest.get("boost_chat_id"):
        await query.answer(texts.BOOST_ALREADY, show_alert=True)
        return

    boosted = await check_user_boosted(context, contest["boost_chat_id"], user.id)
    if not boosted:
        await query.answer(
            texts.BOOST_NOT_DONE.format(link=contest["boost_link"])[:200], show_alert=True
        )
        return

    await db.award_boost_points(contest_id, user.id, config.BOOST_POINTS)
    await query.answer(texts.BOOST_SUCCESS.format(points=config.BOOST_POINTS), show_alert=True)
    await _refresh_post(context, contest_id)


async def on_stars_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⭐ Stars Battle — Stars to'lovi orqali +STARS_VOTE_POINTS ball."""
    from telegram import LabeledPrice
    query = update.callback_query
    user = update.effective_user
    contest_id = int(query.data.split("_")[1])

    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active":
        await query.answer(texts.JOIN_FINISHED, show_alert=True)
        return
    if not await db.is_participant(contest_id, user.id):
        await query.answer(texts.STARS_NOT_JOINED, show_alert=True)
        return

    await query.answer()
    prices = [LabeledPrice(label=texts.STARS_INVOICE_TITLE, amount=config.STARS_VOTE_COST)]
    try:
        await context.bot.send_invoice(
            chat_id=user.id,
            title=texts.STARS_INVOICE_TITLE,
            description=f"Konkurs #{contest_id} uchun +{config.STARS_VOTE_POINTS} ball",
            payload=f"starsvote:{contest_id}:{user.id}",
            provider_token="",
            currency="XTR",
            prices=prices,
        )
    except Exception as e:
        logger.warning(f"Stars invoice yuborilmadi: {e}")
        try:
            me = await context.bot.get_me()
            await context.bot.send_message(
                user.id,
                f"❌ Avval botni ishga tushiring: @{me.username} ga /start yozing, "
                f"so'ng qaytadan Stars yuboring.",
            )
        except Exception:
            pass


async def on_message_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⭐ Stars Battle — postga reaksiya bosgan ishtirokchiga +REACTION_POINTS ball.
    Eslatma: kanal(channel)larda reaksiya muallifi anonim bo'lishi mumkin — bunday holda
    Telegram Bot API foydalanuvchini aniqlamaydi va ball berish imkonsiz bo'ladi."""
    reaction = update.message_reaction
    if not reaction or not reaction.new_reaction or reaction.old_reaction:
        return  # faqat YANGI reaksiya (avval reaksiya bo'lmagan) hisobga olinadi
    user = reaction.user
    if not user:
        return  # anonim reaksiya — muallifni aniqlab bo'lmaydi

    contest = await db.get_contest_by_message(reaction.chat.id, reaction.message_id)
    if not contest or contest["type"] != "stars":
        return
    if not await db.is_participant(contest["id"], user.id):
        return

    awarded = await db.add_point_event(contest["id"], user.id, "reaction", config.REACTION_POINTS, once=True)
    if awarded:
        try:
            await context.bot.send_message(
                user.id, f"👍 Reaksiya uchun rahmat! Sizga +{config.REACTION_POINTS} ball berildi!"
            )
        except Exception:
            pass
        await _refresh_post(context, contest["id"])


async def on_leaderboard_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    contest_id = int(query.data.split("_")[1])
    top = await db.leaderboard(contest_id, limit=10)
    if not top:
        await query.answer(texts.LEADERBOARD_EMPTY, show_alert=True)
        return
    lines = []
    for i, p in enumerate(top, 1):
        u = await db.get_user(p["user_id"])
        uname = (u["username"] if u and u.get("username") else None) or f"ID{p['user_id']}"
        lines.append(f"{i}. {uname} — {p['points']} ball")
    await query.answer("\n".join(lines)[:200], show_alert=True)


def build_post_text(contest: dict, count: int) -> str:
    """Konkurs turi bo'yicha post matnini quradi — yaratishda ham,
    yangilashda ham shu funksiya ishlatiladi (bir xillik uchun)."""
    end_dt = format_dt(contest["end_time"])
    rules = texts.RULES_LINE if contest.get("_required_channels") else ""
    ctype = contest.get("type", "stars")

    if ctype == "vote":
        body = texts.VOTE_POST_TEMPLATE.format(
            winners=contest["winners_count"], end_time=end_dt, count=count, rules=rules,
        )
    elif ctype == "referral":
        body = texts.REFERRAL_POST_TEMPLATE.format(
            winners=contest["winners_count"], end_time=end_dt, count=count, rules=rules,
            referral_points=config.REFERRAL_POINTS,
        )
    elif ctype == "random":
        body = texts.RANDOM_POST_TEMPLATE.format(
            winners=contest["winners_count"], end_time=end_dt, count=count, rules=rules,
        )
    elif ctype == "media":
        body = texts.MEDIA_POST_TEMPLATE.format(
            winners=contest["winners_count"], end_time=end_dt, count=count, rules=rules,
        )
    else:
        body = texts.STARS_POST_TEMPLATE.format(
            winners=contest["winners_count"], end_time=end_dt, count=count, rules=rules,
            stars_points=config.STARS_VOTE_POINTS, reaction_points=config.REACTION_POINTS,
            boost_points=config.BOOST_POINTS,
        )

    custom_text = contest.get("custom_text")
    return f"{custom_text}\n\n{body}" if custom_text else body


async def send_contest_post(bot, chat_id: int, contest: dict, text: str, reply_markup):
    """Konkurs egasi maxsus rasm/video/GIF biriktirgan bo'lsa — shu media bilan,
    aks holda oddiy matn xabar sifatida yuboradi."""
    media_type = contest.get("media_type")
    media_file_id = contest.get("media_file_id")
    caption = text[:1024]  # Telegram caption limiti
    if media_type == "photo" and media_file_id:
        return await bot.send_photo(chat_id, media_file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
    if media_type == "video" and media_file_id:
        return await bot.send_video(chat_id, media_file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
    if media_type == "animation" and media_file_id:
        return await bot.send_animation(chat_id, media_file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
    return await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup)


async def edit_contest_post(bot, chat_id: int, message_id: int, contest: dict, text: str, reply_markup):
    """Media bilan joylangan postlarda caption'ni, oddiy postlarda matnni yangilaydi."""
    if contest.get("media_type") and contest.get("media_file_id"):
        await bot.edit_message_caption(
            chat_id=chat_id, message_id=message_id, caption=text[:1024],
            parse_mode="HTML", reply_markup=reply_markup,
        )
    else:
        await bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=text,
            parse_mode="HTML", reply_markup=reply_markup,
        )


async def _refresh_post(context: ContextTypes.DEFAULT_TYPE, contest_id: int):
    """Kanal postidagi ishtirokchilar sonini yangilaydi (xato bo'lsa e'tibor bermaymiz)."""
    contest = await db.get_contest(contest_id)
    if not contest:
        return
    try:
        count = await db.count_participants(contest_id)
        required = await gather_required_channels(db, contest)
        contest["_required_channels"] = required
        new_text = build_post_text(contest, count)
        ctype = contest.get("type", "stars")

        await edit_contest_post(
            context.bot, contest["chat_id"], contest["message_id"], contest, new_text,
            reply_markup=kb_join_button(contest_id, ctype, bool(contest.get("require_boost"))),
        )
    except Exception as e:
        logger.debug(f"post yangilashda xato (e'tiborsiz qoldirildi): {e}")


# ══════════════════════════════════════════════════════
# G'OLIBLARNI AVTOMATIK ANIQLASH — BALL REYTINGI BO'YICHA
# ══════════════════════════════════════════════════════
async def draw_and_announce_winners(context: ContextTypes.DEFAULT_TYPE, contest_id: int, reason: str):
    import random
    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active":
        return
    await db.update_contest(contest_id, status="finished")
    unschedule_contest_monitor(context.application, contest_id)

    ctype = contest.get("type")
    unit = "ovoz" if ctype == "vote" else ("ta do'st" if ctype == "referral" else "ball")
    count = await db.count_participants(contest_id)

    if ctype == "random":
        # 🎲 Ball/ovoz yo'q — barcha ishtirokchilar orasidan tasodifiy tanlanadi
        all_participants = await db.contest_participants(contest_id)
        n = min(contest["winners_count"], len(all_participants))
        chosen_ids = random.SystemRandom().sample([p["user_id"] for p in all_participants], n) if n else []
        top = [{"user_id": uid, "points": 0} for uid in chosen_ids]
    else:
        top = await db.leaderboard(contest_id, limit=contest["winners_count"])

    lines = []
    for i, p in enumerate(top, 1):
        await db.add_winner(contest_id, p["user_id"], i)
        u = await db.get_user(p["user_id"])
        uname = f"@{u['username']}" if u and u.get("username") else f"ID{p['user_id']}"
        score_suffix = "" if ctype == "random" else f" — {p['points']} {unit}"
        lines.append(f"{i}-o'rin: {uname}{score_suffix}")
        try:
            await context.bot.send_message(
                p["user_id"],
                f"🎉 Tabriklaymiz! Siz <b>#{contest_id}</b> konkursida "
                f"<b>{i}-o'rin</b>ni egalladingiz!{score_suffix}",
                parse_mode="HTML",
            )
        except Exception:
            pass

    winners_text = "\n".join(lines) if lines else "Ishtirokchi bo'lmadi."
    if ctype == "vote":
        header = "REYTING (ovoz soni)"
    elif ctype == "referral":
        header = "eng ko'p taklif qilganlar"
    elif ctype == "random":
        header = "tasodifiy tanlov"
    else:
        header = "ball reytingi"
    try:
        await context.bot.send_message(
            contest["chat_id"],
            f"🏁 <b>KONKURS YAKUNLANDI!</b>\n\nSabab: {reason}\n👥 Jami ishtirokchilar: {count}\n\n"
            f"🏆 <b>G'OLIBLAR ({header} bo'yicha):</b>\n{winners_text}\n\n🎊 Barchaga tabriklar!",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"G'oliblarni e'lon qilishda xato: {e}")

    try:
        await context.bot.send_message(
            contest["owner_id"],
            f"🏁 Sizning #{contest_id} raqamli konkursingiz yakunlandi ({reason}).\n"
            f"👥 Ishtirokchilar: {count}\n🏆 G'oliblar:\n{winners_text}",
            parse_mode="HTML",
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════
# MONITORING JOB — har bir konkurs uchun alohida
# ══════════════════════════════════════════════════════
async def _monitor_tick(context: ContextTypes.DEFAULT_TYPE):
    contest_id = context.job.data["contest_id"]
    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "active":
        try:
            context.job.schedule_removal()
        except Exception:
            pass
        return

    remaining = contest["end_time"] - time.time()
    if remaining <= 0:
        await draw_and_announce_winners(context, contest_id, reason="vaqt tugadi")
        # ❗️ draw_and_announce_winners ichida unschedule_contest_monitor() chaqiriladi va
        # bu job allaqachon shu yerdan (nomi bo'yicha) o'chiriladi — shuning uchun bu yerda
        # context.job.schedule_removal() ni QAYTA chaqirmaymiz (aks holda "JobLookupError" beradi).
        return

    # Real-vaqtda a'zolikni yo'qotganlarni chiqarib tashlash
    required = await gather_required_channels(db, contest)
    if required:
        participants = await db.contest_participants(contest_id)
        for p in participants[:200]:
            still_ok = True
            for ch in required:
                if not await check_user_membership(context, ch["chat_id"], p["user_id"]):
                    still_ok = False
                    break
            if not still_ok:
                await db.remove_participant(contest_id, p["user_id"])
                try:
                    await context.bot.send_message(
                        p["user_id"],
                        "❌ Siz majburiy kanal(lar)dan chiqib ketganingiz uchun "
                        "konkursdan chetlashtirildingiz.",
                    )
                except Exception:
                    pass


def schedule_contest_monitor(application: Application, contest_id: int, interval: int = None):
    jq = application.job_queue
    if jq is None:
        logger.error('JobQueue mavjud emas! pip install "python-telegram-bot[job-queue]" bajaring')
        return
    name = f"contest_monitor_{contest_id}"
    if jq.get_jobs_by_name(name):
        return
    jq.run_repeating(
        _monitor_tick,
        interval=interval or config.MONITOR_INTERVAL_SECONDS,
        first=5,
        name=name,
        data={"contest_id": contest_id},
    )


def unschedule_contest_monitor(application: Application, contest_id: int):
    jq = application.job_queue
    if jq is None:
        return
    for job in jq.get_jobs_by_name(f"contest_monitor_{contest_id}"):
        try:
            job.schedule_removal()
        except Exception:
            pass


async def resume_all_monitors(application: Application):
    """Bot qayta ishga tushganda barcha faol konkurslar uchun monitoringni tiklaydi."""
    contests = await db.active_contests()
    for c in contests:
        schedule_contest_monitor(application, c["id"])
    logger.info(f"{len(contests)} ta faol konkurs monitoring uchun tiklandi.")


# ══════════════════════════════════════════════════════
# 📅 REJALASHTIRILGAN JOYLASH (scheduled publish)
# ══════════════════════════════════════════════════════
async def _publish_tick(context: ContextTypes.DEFAULT_TYPE):
    contest_id = context.job.data["contest_id"]
    contest = await db.get_contest(contest_id)
    if not contest or contest["status"] != "scheduled":
        return

    now = time.time()
    end_time = (
        now + contest["duration_minutes"] * 60
        if contest.get("end_condition") in ("time", "both") or not contest.get("end_condition")
        else None
    )

    contest["_required_channels"] = await gather_required_channels(db, contest)
    post_text = build_post_text(contest, count=0)

    try:
        from keyboards import kb_join_button
        sent = await send_contest_post(
            context.bot, contest["chat_id"], contest, post_text,
            reply_markup=kb_join_button(contest_id, contest.get("type", "stars"), bool(contest.get("require_boost"))),
        )
    except Exception as e:
        logger.error(f"Rejalashtirilgan konkurs postini joylashda xato (id={contest_id}): {e}")
        try:
            await context.bot.send_message(
                contest["owner_id"],
                f"⚠️ #{contest_id} raqamli rejalashtirilgan konkursingiz joylanmadi — bot kanal/guruhda "
                f"admin ekanini va xabar yuborish huquqi borligini tekshiring.",
            )
        except Exception:
            pass
        return

    await db.publish_contest(contest_id, sent.message_id, now, end_time)
    schedule_contest_monitor(context.application, contest_id)

    try:
        await context.bot.send_message(
            contest["owner_id"], f"🚀 #{contest_id} raqamli konkursingiz endi kanalga joylandi!"
        )
    except Exception:
        pass


def schedule_contest_publish(application: Application, contest_id: int, publish_at: float):
    jq = application.job_queue
    if jq is None:
        logger.error('JobQueue mavjud emas!')
        return
    name = f"contest_publish_{contest_id}"
    if jq.get_jobs_by_name(name):
        return
    delay = max(0, publish_at - time.time())
    jq.run_once(_publish_tick, when=delay, name=name, data={"contest_id": contest_id})


async def resume_scheduled_publishes(application: Application):
    """Bot qayta ishga tushganda hali joylanmagan (scheduled) konkurslarni tiklaydi."""
    contests = await db.scheduled_contests()
    for c in contests:
        if c.get("publish_at"):
            schedule_contest_publish(application, c["id"], c["publish_at"])
    logger.info(f"{len(contests)} ta rejalashtirilgan konkurs tiklandi.")


def register(app: Application):
    app.add_handler(CallbackQueryHandler(on_join_click, pattern="^cjoin_"))
    app.add_handler(CallbackQueryHandler(on_join_recheck, pattern="^jrecheck_\\d+$"))
    app.add_handler(CallbackQueryHandler(on_boost_click, pattern="^cboost_"))
    app.add_handler(CallbackQueryHandler(on_stars_click, pattern="^cstars_"))
    app.add_handler(CallbackQueryHandler(on_leaderboard_click, pattern="^clead_"))
    app.add_handler(MessageReactionHandler(on_message_reaction))
