# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 KONFIGURATSIYA
 Barcha sozlamalar shu yerda yoki .env orqali beriladi.
══════════════════════════════════════════════════════════
"""
import os

from dotenv import load_dotenv

load_dotenv()


# ── Asosiy ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
SUPER_ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "8517530604").split(",") if x.strip()
]

DB_PATH = os.getenv("DB_PATH", "data/bot.db")

# ── Konkurs sozlamalari ─────────────────────────────────
# Bepul foydalanuvchi konkursni shuncha vaqtdan ko'p cho'zolmaydi (daqiqada)
FREE_MAX_DURATION_MINUTES = int(os.getenv("FREE_MAX_DURATION_MINUTES", str(7 * 24 * 60)))  # 7 kun
# Pro foydalanuvchi uchun umuman limit (masalan 90 kun) — xohlasa cheksiz qiling
PRO_MAX_DURATION_MINUTES = int(os.getenv("PRO_MAX_DURATION_MINUTES", str(90 * 24 * 60)))

# Har bir konkursga qo'shilishi mumkin bo'lgan sponsor (homiy) kanallar soni
MAX_SPONSOR_CHANNELS_PER_CONTEST = int(os.getenv("MAX_SPONSOR_CHANNELS", "5"))

# Global majburiy kanallar (botning o'z reklama kanallari) — faqat SUPER ADMIN boshqaradi
MAX_GLOBAL_MANDATORY_CHANNELS = 2

# Konkurs monitoring intervali (soniya) — a'zolikni qayta tekshirish
MONITOR_INTERVAL_SECONDS = 20

# Boost qilgan ishtirokchiga beriladigan bonus ball (majburiy emas — faqat reytingni oshiradi)
BOOST_POINTS = int(os.getenv("BOOST_POINTS", "15"))

# ── Konkurs turlari uchun ball sozlamalari ──────────────
# ⭐ Stars Battle turi uchun:
REACTION_POINTS = int(os.getenv("REACTION_POINTS", "1"))       # reaksiya uchun
STARS_VOTE_POINTS = int(os.getenv("STARS_VOTE_POINTS", "5"))   # har bir Stars to'lovi uchun
STARS_VOTE_COST = int(os.getenv("STARS_VOTE_COST", "10"))      # 1 marta Stars yuborish narxi (XTR)

# 🗳 Ovoz to'plash turi uchun sahifadagi nomzodlar soni
VOTE_CANDIDATES_PER_PAGE = 8

# 👥 Referal turi uchun: har bir tasdiqlangan taklif uchun ball
REFERRAL_POINTS = int(os.getenv("REFERRAL_POINTS", "1"))

# 📸 Rasm/Video turi uchun sahifadagi ishlar soni (galereya ko'rinishida)
MEDIA_GALLERY_PER_PAGE = 6

# ── PRO obuna narxlari (Telegram Stars, XTR) ───────────
PRO_PLANS = {
    "pro_30": {"days": 30, "stars": 250, "title": "PRO — 30 kun"},
    "pro_90": {"days": 90, "stars": 600, "title": "PRO — 90 kun"},
    "pro_365": {"days": 365, "stars": 2000, "title": "PRO — 365 kun"},
}

# ── Boshqa ──────────────────────────────────────────────
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# ── Runtime'da to'ldiriladi (main.py post_init) ─────────
BOT_USERNAME = None
