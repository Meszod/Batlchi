# -*- coding: utf-8 -*-
"""Yordamchi funksiyalar: vaqt formatlash, a'zolikni tekshirish, chat helperlar."""
import logging
from datetime import datetime

from telegram import Chat, ChatMember
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

import config

logger = logging.getLogger(__name__)


def format_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} daqiqa"
    if minutes < 1440:
        h = minutes // 60
        m = minutes % 60
        return f"{h} soat" + (f" {m} daq" if m else "")
    days = minutes // 1440
    rem_h = (minutes % 1440) // 60
    return f"{days} kun" + (f" {rem_h} soat" if rem_h else "")


def format_remaining(seconds: float) -> str:
    if seconds <= 0:
        return "0:00"
    seconds = int(seconds)
    d, seconds = divmod(seconds, 86400)
    h, seconds = divmod(seconds, 3600)
    m, s = divmod(seconds, 60)
    if d:
        return f"{d}k {h:02d}:{m:02d}:{s:02d}"
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_dt(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")


async def get_chat_from_forward(update_message) -> Chat | None:
    """Forward qilingan xabardan manba chat (kanal/guruh)ni aniqlaydi."""
    fwd_chat = getattr(update_message, "forward_from_chat", None)
    if fwd_chat:
        return fwd_chat
    # Ba'zi mijozlarda forward_origin orqali keladi (PTB v20+)
    origin = getattr(update_message, "forward_origin", None)
    if origin is not None:
        chat = getattr(origin, "chat", None)
        if chat:
            return chat
    return None


async def is_bot_admin_in_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    try:
        me = await context.bot.get_me()
        member = await context.bot.get_chat_member(chat_id, me.id)
        return member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER)
    except (BadRequest, Forbidden) as e:
        logger.debug(f"is_bot_admin_in_chat xato: {e}")
        return False


async def is_user_admin_in_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER)
    except (BadRequest, Forbidden) as e:
        logger.debug(f"is_user_admin_in_chat xato: {e}")
        return False


async def get_chat_invite_link(context: ContextTypes.DEFAULT_TYPE, chat) -> str:
    """Kanal/guruh uchun taklif havolasini qaytaradi (username bo'lsa t.me/username,
    bo'lmasa export_chat_invite_link orqali)."""
    if getattr(chat, "username", None):
        return f"https://t.me/{chat.username}"
    try:
        link = await context.bot.export_chat_invite_link(chat.id)
        return link
    except Exception as e:
        logger.warning(f"invite link olinmadi: {e}")
        return ""


async def check_user_membership(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """User berilgan chatga a'zomi?"""
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER,
        )
    except (BadRequest, Forbidden):
        return False


async def check_user_boosted(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """User berilgan kanalni boost qilganmi? (Bot API 7.5+, getUserChatBoosts)"""
    try:
        boosts = await context.bot.get_user_chat_boosts(chat_id, user_id)
        return bool(boosts and boosts.boosts)
    except Exception as e:
        logger.debug(f"boost tekshiruvi imkonsiz: {e}")
        # Agar API mavjud bo'lmasa yoki xato bo'lsa — talabni bloklamaslik uchun True qaytaramiz
        return True


async def gather_required_channels(db, contest: dict) -> list:
    """Konkurs uchun barcha majburiy kanallar ro'yxatini (global + sponsor) qaytaradi."""
    channels = []
    if contest.get("use_global_channels"):
        for ch in await db.list_global_channels():
            channels.append({"chat_id": ch["chat_id"], "title": ch["title"], "link": ch["link"]})
    for sp in contest.get("sponsor_channels", []):
        channels.append(sp)
    return channels


def resolve_chat_display_link(chat) -> str:
    if getattr(chat, "username", None):
        return f"https://t.me/{chat.username}"
    return ""
