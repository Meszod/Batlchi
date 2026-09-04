# -*- coding: utf-8 -*-
"""Barcha inline/reply klaviaturalar shu yerda yig'ilgan."""
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

import config


# ══════════════════════════════════════════════════════
# ASOSIY MENYU (reply keyboard — hammaga)
# ══════════════════════════════════════════════════════
def kb_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        ["➕ Konkurs qilish"],
        ["📋 Mening konkurslarim", "💎 PRO"],
        ["ℹ️ Yordam"],
    ]
    if is_admin:
        rows.append(["🔧 Admin Panel"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def kb_cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")]])


def kb_type_select() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗳 Ovoz to'plash", callback_data="ctype_vote")],
        [InlineKeyboardButton("⭐ Stars Battle", callback_data="ctype_stars")],
        [InlineKeyboardButton("👥 Referal", callback_data="ctype_referral")],
        [InlineKeyboardButton("🎲 Oddiy Random", callback_data="ctype_random")],
        [InlineKeyboardButton("📸 Rasm/Video", callback_data="ctype_media")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")],
    ])


def kb_sponsor_step() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tayyor / Keyingi qadam", callback_data="sponsor_done")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")],
    ])


def kb_boost_step() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Kerak emas", callback_data="boost_skip")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")],
    ])


def kb_duration(is_pro: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("10 daq", callback_data="dur_10"),
         InlineKeyboardButton("30 daq", callback_data="dur_30"),
         InlineKeyboardButton("1 soat", callback_data="dur_60")],
        [InlineKeyboardButton("6 soat", callback_data="dur_360"),
         InlineKeyboardButton("1 kun", callback_data="dur_1440"),
         InlineKeyboardButton("3 kun", callback_data="dur_4320")],
        [InlineKeyboardButton("7 kun", callback_data="dur_10080")],
    ]
    if is_pro:
        rows.append([
            InlineKeyboardButton("14 kun 💎", callback_data="dur_20160"),
            InlineKeyboardButton("30 kun 💎", callback_data="dur_43200"),
        ])
    rows.append([InlineKeyboardButton("✏️ Boshqa (custom)", callback_data="dur_custom")])
    rows.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")])
    return InlineKeyboardMarkup(rows)


def kb_winners_count() -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(str(n), callback_data=f"win_{n}") for n in (1, 2, 3)
    ], [
        InlineKeyboardButton(str(n), callback_data=f"win_{n}") for n in (5, 10)
    ], [InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")]]
    return InlineKeyboardMarkup(rows)


def kb_end_condition() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏰ Vaqt bo'yicha", callback_data="endc_time")],
        [InlineKeyboardButton("👥 Ishtirokchilar soni bo'yicha", callback_data="endc_count")],
        [InlineKeyboardButton("🔀 Ikkalasi ham", callback_data="endc_both")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")],
    ])


def kb_target_count() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(str(n), callback_data=f"tcount_{n}") for n in (10, 25, 50)],
        [InlineKeyboardButton(str(n), callback_data=f"tcount_{n}") for n in (100, 500, 1000)],
        [InlineKeyboardButton("✏️ Boshqa (custom)", callback_data="tcount_custom")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")],
    ]
    return InlineKeyboardMarkup(rows)


def kb_publish_timing() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Hozir joylash", callback_data="pub_now")],
        [InlineKeyboardButton("⏰ Vaqt belgilash", callback_data="pub_schedule")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")],
    ])


def kb_schedule_presets() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1 soatdan keyin", callback_data="sched_60"),
         InlineKeyboardButton("6 soatdan keyin", callback_data="sched_360")],
        [InlineKeyboardButton("Ertaga shu vaqtda", callback_data="sched_1440")],
        [InlineKeyboardButton("✏️ Aniq sana kiritish", callback_data="sched_custom")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")],
    ])


def kb_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Boshlash", callback_data="confirm_start")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="wizard_cancel")],
    ])


# ══════════════════════════════════════════════════════
# KONKURS POST (kanal/guruh ichida)
# ══════════════════════════════════════════════════════
def kb_join_button(contest_id: int, contest_type: str = "stars", boost_enabled: bool = False) -> InlineKeyboardMarkup:
    import config
    rows = [[InlineKeyboardButton("🎉 Konkursga qo'shilish", callback_data=f"cjoin_{contest_id}")]]
    if contest_type == "vote":
        rows.append([InlineKeyboardButton("🗳 Ovoz berish", callback_data=f"vlist_{contest_id}_0")])
    elif contest_type == "referral":
        rows.append([InlineKeyboardButton("🔗 Taklif havolamni olish", callback_data=f"creflink_{contest_id}")])
    elif contest_type == "random":
        pass  # faqat qo'shilish tugmasi — ball/ovoz tizimi yo'q
    elif contest_type == "media":
        rows.append([InlineKeyboardButton("🖼 Ishlarni ko'rish", callback_data=f"mgallery_{contest_id}_0")])
    else:  # stars
        rows.append([InlineKeyboardButton(
            f"⭐ Stars yuborish (+{config.STARS_VOTE_POINTS} ball)", callback_data=f"cstars_{contest_id}"
        )])
        if boost_enabled:
            rows.append([InlineKeyboardButton(
                f"🚀 Boost qilib +{config.BOOST_POINTS} ball olish", callback_data=f"cboost_{contest_id}"
            )])
    if contest_type != "random":
        rows.append([InlineKeyboardButton("📊 Reyting", callback_data=f"clead_{contest_id}")])
    return InlineKeyboardMarkup(rows)


def kb_media_like(contest_id: int, submission_id: int, likes: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"❤️ Layk ({likes})", callback_data=f"mlike_{submission_id}")
    ]])


def kb_media_gallery(contest_id: int, submissions: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    for s in submissions:
        name = s.get("display_name", f"ID{s['user_id']}")
        rows.append([InlineKeyboardButton(
            f"🖼 {name} — ❤️{s['likes_count']}", callback_data=f"mview_{contest_id}_{s['id']}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"mgallery_{contest_id}_{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"mgallery_{contest_id}_{page+1}"))
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(rows)


def kb_vote_candidates(
    contest_id: int, candidates: list, page: int, total_pages: int,
    channel_url: str = None,
) -> InlineKeyboardMarkup:
    rows = []
    for c in candidates:
        name = c.get("display_name", f"ID{c['user_id']}")
        rows.append([InlineKeyboardButton(
            f"👤 {name} — {c['points']} ovoz", callback_data=f"vcand_{contest_id}_{c['user_id']}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"vlist_{contest_id}_{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"vlist_{contest_id}_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 Yopish", callback_data=f"vclose_{contest_id}")])
    if channel_url:
        rows.append([InlineKeyboardButton("📢 Kanalga o'tish", url=channel_url)])
    return InlineKeyboardMarkup(rows)


# ══════════════════════════════════════════════════════
# FOYDALANUVCHI — MENING KONKURSLARIM
# ══════════════════════════════════════════════════════
def kb_my_contests(contests: list) -> InlineKeyboardMarkup:
    rows = []
    for c in contests:
        icon = "🟢" if c["status"] == "active" else ("🔴" if c["status"] == "cancelled" else "⚪️")
        rows.append([InlineKeyboardButton(
            f"{icon} #{c['id']} — {c['chat_title'] or c['chat_id']}",
            callback_data=f"mc_view_{c['id']}",
        )])
    return InlineKeyboardMarkup(rows) if rows else None


def kb_contest_manage(contest_id: int, status: str, require_boost: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if status == "active":
        rows.append([
            InlineKeyboardButton("🏁 Yakunlash (g'oliblarni e'lon qilish)", callback_data=f"mc_stop_{contest_id}"),
            InlineKeyboardButton("➕ Cho'zish", callback_data=f"mc_extend_{contest_id}"),
        ])
        rows.append([
            InlineKeyboardButton("📊 Reyting", callback_data=f"mc_lead_{contest_id}"),
        ])
        if require_boost:
            rows.append([InlineKeyboardButton(
                "🚀 Boost bonusini o'chirish", callback_data=f"mc_noboost_{contest_id}"
            )])
    else:
        rows.append([InlineKeyboardButton("📊 Reyting / Natijalar", callback_data=f"mc_lead_{contest_id}")])
    rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="mc_back")])
    return InlineKeyboardMarkup(rows)


def kb_extend_options(contest_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("+30 daq", callback_data=f"mcext_{contest_id}_30"),
         InlineKeyboardButton("+1 soat", callback_data=f"mcext_{contest_id}_60")],
        [InlineKeyboardButton("+1 kun", callback_data=f"mcext_{contest_id}_1440"),
         InlineKeyboardButton("+1 hafta", callback_data=f"mcext_{contest_id}_10080")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data=f"mc_view_{contest_id}")],
    ])


# ══════════════════════════════════════════════════════
# PRO
# ══════════════════════════════════════════════════════
def kb_pro_plans() -> InlineKeyboardMarkup:
    rows = []
    for key, plan in config.PRO_PLANS.items():
        rows.append([InlineKeyboardButton(
            f"{plan['title']} — ⭐️ {plan['stars']}", callback_data=f"buypro_{key}"
        )])
    return InlineKeyboardMarkup(rows)


# ══════════════════════════════════════════════════════
# SUPER ADMIN PANEL
# ══════════════════════════════════════════════════════
def kb_admin_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Global kanallar", callback_data="adm_channels"),
         InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="adm_users")],
        [InlineKeyboardButton("🔥 Barcha konkurslar", callback_data="adm_contests"),
         InlineKeyboardButton("💎 PRO boshqaruvi", callback_data="adm_pro")],
        [InlineKeyboardButton("📊 Statistika", callback_data="adm_stats"),
         InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast")],
    ])


def kb_admin_channels(channels: list) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        rows.append([InlineKeyboardButton(
            f"❌ {ch['title']}", callback_data=f"adm_delch_{ch['chat_id']}"
        )])
    if len(channels) < config.MAX_GLOBAL_MANDATORY_CHANNELS:
        rows.append([InlineKeyboardButton("➕ Kanal qo'shish", callback_data="adm_addch")])
    rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")])
    return InlineKeyboardMarkup(rows)


def kb_admin_users() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban", callback_data="adm_ban"),
         InlineKeyboardButton("✅ Unban", callback_data="adm_unban")],
        [InlineKeyboardButton("⚠️ Ogohlantirish", callback_data="adm_warn"),
         InlineKeyboardButton("👤 Ma'lumot", callback_data="adm_info")],
        [InlineKeyboardButton("🏆 TOP", callback_data="adm_top")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")],
    ])


def kb_admin_pro() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ PRO berish", callback_data="adm_grantpro"),
         InlineKeyboardButton("➖ PRO olib tashlash", callback_data="adm_revokepro")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")],
    ])


def kb_back(target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=target)]])
