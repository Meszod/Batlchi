# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
 DATABASE LAYER (SQLite, aiosqlite orqali)
 Butun bot holati shu yerda saqlanadi — restart bo'lsa ham
 hech narsa yo'qolmaydi.
══════════════════════════════════════════════════════════
"""
import json
import logging
import os
import time
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


def _referral_points() -> int:
    """Lazy import — config.py yuklanish tartibida db.py oldinroq import bo'lishi mumkin."""
    import config
    return config.REFERRAL_POINTS

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY,
    username      TEXT,
    first_name    TEXT,
    is_banned     INTEGER DEFAULT 0,
    warnings      INTEGER DEFAULT 0,
    is_pro        INTEGER DEFAULT 0,
    pro_until     REAL DEFAULT 0,
    joined_at     REAL,
    last_activity REAL
);

CREATE TABLE IF NOT EXISTS contests (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id           INTEGER,
    type               TEXT DEFAULT 'stars',   -- 'vote' (Ovoz to'plash) | 'stars' (Stars Battle)
    chat_id            INTEGER,
    chat_title         TEXT,
    chat_link          TEXT,
    message_id         INTEGER,
    sponsor_channels   TEXT DEFAULT '[]',   -- JSON: [{"chat_id":..,"title":..,"link":..}]
    boost_chat_id      INTEGER,
    boost_link         TEXT,
    require_boost      INTEGER DEFAULT 0,
    use_global_channels INTEGER DEFAULT 1,   -- pro bo'lsa 0 qilinadi
    winners_count      INTEGER DEFAULT 1,
    duration_minutes   INTEGER,
    end_condition      TEXT DEFAULT 'time',    -- 'time' | 'count' | 'both'
    target_participants INTEGER,               -- 'count'/'both' rejimida ishlatiladi
    publish_at         REAL,                   -- NULL = darhol joylash; aks holda rejalashtirilgan vaqt
    start_time         REAL,
    end_time           REAL,
    status             TEXT DEFAULT 'active', -- scheduled/active/finished/cancelled
    custom_text        TEXT,                   -- egasi kiritgan tanlov matni (ixtiyoriy)
    media_type         TEXT,                   -- 'photo' | 'video' | 'animation' | NULL
    media_file_id      TEXT,                   -- Telegram file_id (bitta media fayl)
    created_at         REAL
);

CREATE TABLE IF NOT EXISTS votes (
    contest_id   INTEGER,
    voter_id     INTEGER,
    candidate_id INTEGER,
    voted_at     REAL,
    PRIMARY KEY (contest_id, voter_id)
);

CREATE TABLE IF NOT EXISTS point_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id  INTEGER,
    user_id     INTEGER,
    source      TEXT,        -- 'boost' | 'reaction' | 'stars'
    points      INTEGER,
    created_at  REAL
);

CREATE TABLE IF NOT EXISTS referrals (
    contest_id       INTEGER,
    referred_user_id INTEGER,
    referrer_id      INTEGER,
    created_at       REAL,
    PRIMARY KEY (contest_id, referred_user_id)
);

CREATE TABLE IF NOT EXISTS submissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id  INTEGER,
    user_id     INTEGER,
    file_id     TEXT,
    media_type  TEXT,        -- 'photo' | 'video'
    chat_id     INTEGER,
    message_id  INTEGER,
    likes_count INTEGER DEFAULT 0,
    created_at  REAL,
    UNIQUE(contest_id, user_id)
);

CREATE TABLE IF NOT EXISTS submission_likes (
    submission_id INTEGER,
    liker_id      INTEGER,
    liked_at      REAL,
    PRIMARY KEY (submission_id, liker_id)
);

CREATE TABLE IF NOT EXISTS participants (
    contest_id  INTEGER,
    user_id     INTEGER,
    joined_at   REAL,
    points      INTEGER DEFAULT 0,
    boosted     INTEGER DEFAULT 0,
    PRIMARY KEY (contest_id, user_id)
);

CREATE TABLE IF NOT EXISTS pending_referrals (
    user_id     INTEGER PRIMARY KEY,
    contest_id  INTEGER,
    referrer_id INTEGER,
    created_at  REAL
);

CREATE TABLE IF NOT EXISTS winners (
    contest_id  INTEGER,
    user_id     INTEGER,
    position    INTEGER,
    chosen_at   REAL,
    PRIMARY KEY (contest_id, user_id)
);

CREATE TABLE IF NOT EXISTS global_channels (
    chat_id   INTEGER PRIMARY KEY,
    title     TEXT,
    link      TEXT,
    added_by  INTEGER,
    added_at  REAL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


class Database:
    def __init__(self, path: Optional[str] = None):
        self.path = path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self, path: Optional[str] = None):
        self.path = path or self.path
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()
        # ── eski bazalar uchun xavfsiz migratsiya (ustunlar mavjud bo'lmasa qo'shadi) ──
        for ddl in (
            "ALTER TABLE participants ADD COLUMN points INTEGER DEFAULT 0",
            "ALTER TABLE participants ADD COLUMN boosted INTEGER DEFAULT 0",
            "ALTER TABLE contests ADD COLUMN type TEXT DEFAULT 'stars'",
            "ALTER TABLE contests ADD COLUMN end_condition TEXT DEFAULT 'time'",
            "ALTER TABLE contests ADD COLUMN target_participants INTEGER",
            "ALTER TABLE contests ADD COLUMN publish_at REAL",
            "ALTER TABLE contests ADD COLUMN custom_text TEXT",
            "ALTER TABLE contests ADD COLUMN media_type TEXT",
            "ALTER TABLE contests ADD COLUMN media_file_id TEXT",
        ):
            try:
                await self._conn.execute(ddl)
                await self._conn.commit()
            except Exception:
                pass  # ustun allaqachon mavjud
        logger.info(f"DB ulandi: {self.path}")

    async def close(self):
        if self._conn:
            await self._conn.close()

    # ── umumiy yordamchilar ────────────────────────────
    async def execute(self, query: str, params: tuple = ()):
        cur = await self._conn.execute(query, params)
        await self._conn.commit()
        return cur

    async def fetchone(self, query: str, params: tuple = ()):
        cur = await self._conn.execute(query, params)
        row = await cur.fetchone()
        return dict(row) if row else None

    async def fetchall(self, query: str, params: tuple = ()):
        cur = await self._conn.execute(query, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════
    # USERS
    # ══════════════════════════════════════════════════
    async def upsert_user(self, user_id: int, username: str, first_name: str):
        now = time.time()
        row = await self.fetchone("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if row:
            await self.execute(
                "UPDATE users SET username=?, first_name=?, last_activity=? WHERE user_id=?",
                (username, first_name, now, user_id),
            )
            return False  # allaqachon mavjud
        await self.execute(
            "INSERT INTO users (user_id, username, first_name, joined_at, last_activity) "
            "VALUES (?,?,?,?,?)",
            (user_id, username, first_name, now, now),
        )
        return True  # yangi foydalanuvchi

    async def get_user(self, user_id: int) -> Optional[dict]:
        return await self.fetchone("SELECT * FROM users WHERE user_id=?", (user_id,))

    async def touch_activity(self, user_id: int):
        await self.execute(
            "UPDATE users SET last_activity=? WHERE user_id=?", (time.time(), user_id)
        )

    async def set_ban(self, user_id: int, banned: bool):
        await self.execute("UPDATE users SET is_banned=? WHERE user_id=?", (int(banned), user_id))

    async def add_warning(self, user_id: int) -> int:
        await self.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id=?", (user_id,))
        u = await self.get_user(user_id)
        return u["warnings"] if u else 0

    async def is_banned(self, user_id: int) -> bool:
        u = await self.get_user(user_id)
        return bool(u and u["is_banned"])

    async def set_pro(self, user_id: int, days: int):
        u = await self.get_user(user_id)
        now = time.time()
        base = now
        if u and u["pro_until"] and u["pro_until"] > now:
            base = u["pro_until"]
        new_until = base + days * 86400
        await self.execute(
            "UPDATE users SET is_pro=1, pro_until=? WHERE user_id=?", (new_until, user_id)
        )
        return new_until

    async def revoke_pro(self, user_id: int):
        await self.execute(
            "UPDATE users SET is_pro=0, pro_until=0 WHERE user_id=?", (user_id,)
        )

    async def is_pro(self, user_id: int) -> bool:
        u = await self.get_user(user_id)
        if not u:
            return False
        if u["is_pro"] and u["pro_until"] and u["pro_until"] > time.time():
            return True
        if u["is_pro"] and u["pro_until"] and u["pro_until"] <= time.time():
            await self.execute(
                "UPDATE users SET is_pro=0 WHERE user_id=?", (user_id,)
            )
        return False

    async def all_user_ids(self) -> list:
        rows = await self.fetchall("SELECT user_id FROM users WHERE is_banned=0")
        return [r["user_id"] for r in rows]

    async def count_users(self) -> int:
        r = await self.fetchone("SELECT COUNT(*) c FROM users")
        return r["c"] if r else 0

    async def count_pro_users(self) -> int:
        r = await self.fetchone(
            "SELECT COUNT(*) c FROM users WHERE is_pro=1 AND pro_until > ?", (time.time(),)
        )
        return r["c"] if r else 0

    async def top_users(self, limit=10) -> list:
        return await self.fetchall(
            """SELECT u.user_id, u.username,
                      (SELECT COUNT(*) FROM participants p WHERE p.user_id=u.user_id) as joined,
                      (SELECT COUNT(*) FROM winners w WHERE w.user_id=u.user_id) as won
               FROM users u ORDER BY joined DESC LIMIT ?""",
            (limit,),
        )

    # ══════════════════════════════════════════════════
    # GLOBAL MAJBURIY KANALLAR
    # ══════════════════════════════════════════════════
    async def add_global_channel(self, chat_id: int, title: str, link: str, added_by: int):
        await self.execute(
            "INSERT OR REPLACE INTO global_channels (chat_id, title, link, added_by, added_at) "
            "VALUES (?,?,?,?,?)",
            (chat_id, title, link, added_by, time.time()),
        )

    async def remove_global_channel(self, chat_id: int):
        await self.execute("DELETE FROM global_channels WHERE chat_id=?", (chat_id,))

    async def list_global_channels(self) -> list:
        return await self.fetchall("SELECT * FROM global_channels ORDER BY added_at")

    async def count_global_channels(self) -> int:
        r = await self.fetchone("SELECT COUNT(*) c FROM global_channels")
        return r["c"] if r else 0

    # ══════════════════════════════════════════════════
    # KONKURSLAR (CONTESTS)
    # ══════════════════════════════════════════════════
    async def create_contest(self, **kw) -> int:
        kw.setdefault("sponsor_channels", "[]")
        if not isinstance(kw["sponsor_channels"], str):
            kw["sponsor_channels"] = json.dumps(kw["sponsor_channels"], ensure_ascii=False)
        kw["created_at"] = time.time()
        cols = ",".join(kw.keys())
        qs = ",".join("?" for _ in kw)
        cur = await self.execute(
            f"INSERT INTO contests ({cols}) VALUES ({qs})", tuple(kw.values())
        )
        return cur.lastrowid

    async def get_contest(self, contest_id: int) -> Optional[dict]:
        c = await self.fetchone("SELECT * FROM contests WHERE id=?", (contest_id,))
        if c:
            c["sponsor_channels"] = json.loads(c["sponsor_channels"] or "[]")
        return c

    async def update_contest(self, contest_id: int, **kw):
        if "sponsor_channels" in kw and not isinstance(kw["sponsor_channels"], str):
            kw["sponsor_channels"] = json.dumps(kw["sponsor_channels"], ensure_ascii=False)
        sets = ",".join(f"{k}=?" for k in kw)
        await self.execute(
            f"UPDATE contests SET {sets} WHERE id=?", (*kw.values(), contest_id)
        )

    async def get_contest_by_message(self, chat_id: int, message_id: int) -> Optional[dict]:
        c = await self.fetchone(
            "SELECT * FROM contests WHERE chat_id=? AND message_id=? AND status='active'",
            (chat_id, message_id),
        )
        if c:
            c["sponsor_channels"] = json.loads(c["sponsor_channels"] or "[]")
        return c

    async def active_contests(self) -> list:
        rows = await self.fetchall("SELECT * FROM contests WHERE status='active'")
        for r in rows:
            r["sponsor_channels"] = json.loads(r["sponsor_channels"] or "[]")
        return rows

    async def scheduled_contests(self) -> list:
        rows = await self.fetchall("SELECT * FROM contests WHERE status='scheduled'")
        for r in rows:
            r["sponsor_channels"] = json.loads(r["sponsor_channels"] or "[]")
        return rows

    async def publish_contest(self, contest_id: int, message_id: int, start_time: float, end_time: Optional[float]):
        """Rejalashtirilgan konkursni haqiqatan e'lon qilingan vaqtga bog'lab faollashtiradi."""
        await self.execute(
            "UPDATE contests SET status='active', message_id=?, start_time=?, end_time=?, "
            "publish_at=NULL WHERE id=?",
            (message_id, start_time, end_time, contest_id),
        )

    async def contests_by_owner(self, owner_id: int) -> list:
        rows = await self.fetchall(
            "SELECT * FROM contests WHERE owner_id=? ORDER BY id DESC LIMIT 20", (owner_id,)
        )
        for r in rows:
            r["sponsor_channels"] = json.loads(r["sponsor_channels"] or "[]")
        return rows

    async def count_contests(self) -> int:
        r = await self.fetchone("SELECT COUNT(*) c FROM contests")
        return r["c"] if r else 0

    # ── ishtirokchilar ──────────────────────────────────
    async def add_participant(self, contest_id: int, user_id: int):
        await self.execute(
            "INSERT OR IGNORE INTO participants (contest_id, user_id, joined_at) VALUES (?,?,?)",
            (contest_id, user_id, time.time()),
        )

    async def remove_participant(self, contest_id: int, user_id: int):
        await self.execute(
            "DELETE FROM participants WHERE contest_id=? AND user_id=?", (contest_id, user_id)
        )

    async def is_participant(self, contest_id: int, user_id: int) -> bool:
        r = await self.fetchone(
            "SELECT 1 FROM participants WHERE contest_id=? AND user_id=?", (contest_id, user_id)
        )
        return bool(r)

    async def contest_participants(self, contest_id: int) -> list:
        return await self.fetchall(
            "SELECT * FROM participants WHERE contest_id=? ORDER BY joined_at", (contest_id,)
        )

    async def count_participants(self, contest_id: int) -> int:
        r = await self.fetchone(
            "SELECT COUNT(*) c FROM participants WHERE contest_id=?", (contest_id,)
        )
        return r["c"] if r else 0

    # ── ball / boost bonusi ──────────────────────────────
    async def is_boosted(self, contest_id: int, user_id: int) -> bool:
        r = await self.fetchone(
            "SELECT boosted FROM participants WHERE contest_id=? AND user_id=?",
            (contest_id, user_id),
        )
        return bool(r and r["boosted"])

    async def award_boost_points(self, contest_id: int, user_id: int, points: int) -> bool:
        """Boost uchun ball beradi. Agar avval berilgan bo'lsa False qaytaradi (qayta bermaydi)."""
        if await self.is_boosted(contest_id, user_id):
            return False
        await self.execute(
            "UPDATE participants SET boosted=1, points = points + ? WHERE contest_id=? AND user_id=?",
            (points, contest_id, user_id),
        )
        return True

    async def leaderboard(self, contest_id: int, limit: Optional[int] = None) -> list:
        q = (
            "SELECT * FROM participants WHERE contest_id=? "
            "ORDER BY points DESC, joined_at ASC"
        )
        params = (contest_id,)
        if limit:
            q += " LIMIT ?"
            params = (contest_id, limit)
        return await self.fetchall(q, params)

    async def get_participant(self, contest_id: int, user_id: int) -> Optional[dict]:
        return await self.fetchone(
            "SELECT * FROM participants WHERE contest_id=? AND user_id=?", (contest_id, user_id)
        )

    # ── umumiy ball voqealari (Stars Battle: boost/reaction/stars) ──────
    async def has_point_event(self, contest_id: int, user_id: int, source: str) -> bool:
        r = await self.fetchone(
            "SELECT 1 FROM point_events WHERE contest_id=? AND user_id=? AND source=?",
            (contest_id, user_id, source),
        )
        return bool(r)

    async def add_point_event(
        self, contest_id: int, user_id: int, source: str, points: int, once: bool = True
    ) -> bool:
        """Ball voqeasini qo'shadi. once=True bo'lsa, shu source uchun faqat bir marta beriladi
        (masalan boost, reaction). once=False bo'lsa har safar qo'shilaveradi (masalan stars)."""
        if once and await self.has_point_event(contest_id, user_id, source):
            return False
        await self.execute(
            "INSERT INTO point_events (contest_id, user_id, source, points, created_at) "
            "VALUES (?,?,?,?,?)",
            (contest_id, user_id, source, points, time.time()),
        )
        await self.execute(
            "UPDATE participants SET points = points + ? WHERE contest_id=? AND user_id=?",
            (points, contest_id, user_id),
        )
        return True

    # ── 🗳 Ovoz to'plash tizimi ──────────────────────────
    async def get_vote(self, contest_id: int, voter_id: int) -> Optional[dict]:
        return await self.fetchone(
            "SELECT * FROM votes WHERE contest_id=? AND voter_id=?", (contest_id, voter_id)
        )

    async def cast_vote(self, contest_id: int, voter_id: int, candidate_id: int) -> str:
        """Ovoz beradi. Qaytaradi: 'new' (yangi ovoz), 'changed' (ovoz almashtirildi),
        'same' (allaqachon shu nomzodga ovoz bergan)."""
        existing = await self.get_vote(contest_id, voter_id)
        if existing and existing["candidate_id"] == candidate_id:
            return "same"
        if existing:
            await self.execute(
                "UPDATE participants SET points = points - 1 WHERE contest_id=? AND user_id=?",
                (contest_id, existing["candidate_id"]),
            )
        await self.execute(
            "INSERT OR REPLACE INTO votes (contest_id, voter_id, candidate_id, voted_at) "
            "VALUES (?,?,?,?)",
            (contest_id, voter_id, candidate_id, time.time()),
        )
        await self.execute(
            "UPDATE participants SET points = points + 1 WHERE contest_id=? AND user_id=?",
            (contest_id, candidate_id),
        )
        return "changed" if existing else "new"

    async def candidates_page(self, contest_id: int, page: int, per_page: int) -> tuple:
        """(nomzodlar_royxati, jami_sahifalar) — ovoz soni bo'yicha kamayish tartibida."""
        total = await self.count_participants(contest_id)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = max(0, min(page, total_pages - 1))
        rows = await self.fetchall(
            "SELECT * FROM participants WHERE contest_id=? "
            "ORDER BY points DESC, joined_at ASC LIMIT ? OFFSET ?",
            (contest_id, per_page, page * per_page),
        )
        return rows, total_pages, page

    # ── g'oliblar ────────────────────────────────────────
    async def add_winner(self, contest_id: int, user_id: int, position: int):
        await self.execute(
            "INSERT OR REPLACE INTO winners (contest_id, user_id, position, chosen_at) "
            "VALUES (?,?,?,?)",
            (contest_id, user_id, position, time.time()),
        )

    async def contest_winners(self, contest_id: int) -> list:
        return await self.fetchall(
            "SELECT * FROM winners WHERE contest_id=? ORDER BY position", (contest_id,)
        )

    # ══════════════════════════════════════════════════
    # 👥 REFERAL TIZIMI
    # ══════════════════════════════════════════════════
    async def set_pending_referral(self, user_id: int, contest_id: int, referrer_id: int):
        """Kim kimni taklif qilganini DOIMIY saqlaydi (bot qayta ishga tushsa ham yo'qolmasin)."""
        await self.execute(
            "INSERT OR REPLACE INTO pending_referrals (user_id, contest_id, referrer_id, created_at) "
            "VALUES (?,?,?,?)",
            (user_id, contest_id, referrer_id, time.time()),
        )

    async def pop_pending_referral(self, user_id: int) -> Optional[dict]:
        row = await self.fetchone(
            "SELECT * FROM pending_referrals WHERE user_id=?", (user_id,)
        )
        if row:
            await self.execute("DELETE FROM pending_referrals WHERE user_id=?", (user_id,))
        return dict(row) if row else None

    async def register_referral(self, contest_id: int, referred_user_id: int, referrer_id: int) -> bool:
        """Yangi taklif qilinganni ro'yxatga oladi va referrerga ball beradi.
        Bir kishi bir konkursda faqat 1 marta 'taklif qilingan' bo'la oladi (PK)."""
        existing = await self.fetchone(
            "SELECT 1 FROM referrals WHERE contest_id=? AND referred_user_id=?",
            (contest_id, referred_user_id),
        )
        if existing:
            return False
        if referred_user_id == referrer_id:
            return False
        await self.execute(
            "INSERT INTO referrals (contest_id, referred_user_id, referrer_id, created_at) "
            "VALUES (?,?,?,?)",
            (contest_id, referred_user_id, referrer_id, time.time()),
        )
        await self.execute(
            "UPDATE participants SET points = points + ? WHERE contest_id=? AND user_id=?",
            (_referral_points(), contest_id, referrer_id),
        )
        return True

    async def count_referrals(self, contest_id: int, referrer_id: int) -> int:
        r = await self.fetchone(
            "SELECT COUNT(*) c FROM referrals WHERE contest_id=? AND referrer_id=?",
            (contest_id, referrer_id),
        )
        return r["c"] if r else 0

    # ══════════════════════════════════════════════════
    # 📸 RASM/VIDEO (MEDIA) BATTLE
    # ══════════════════════════════════════════════════
    async def create_submission(
        self, contest_id: int, user_id: int, file_id: str, media_type: str,
        chat_id: int, message_id: int,
    ) -> Optional[int]:
        existing = await self.fetchone(
            "SELECT id FROM submissions WHERE contest_id=? AND user_id=?", (contest_id, user_id)
        )
        if existing:
            return None
        cur = await self.execute(
            "INSERT INTO submissions (contest_id, user_id, file_id, media_type, chat_id, "
            "message_id, likes_count, created_at) VALUES (?,?,?,?,?,?,0,?)",
            (contest_id, user_id, file_id, media_type, chat_id, message_id, time.time()),
        )
        return cur.lastrowid

    async def get_submission(self, submission_id: int) -> Optional[dict]:
        return await self.fetchone("SELECT * FROM submissions WHERE id=?", (submission_id,))

    async def get_submission_by_user(self, contest_id: int, user_id: int) -> Optional[dict]:
        return await self.fetchone(
            "SELECT * FROM submissions WHERE contest_id=? AND user_id=?", (contest_id, user_id)
        )

    async def contest_submissions(self, contest_id: int) -> list:
        return await self.fetchall(
            "SELECT * FROM submissions WHERE contest_id=? ORDER BY likes_count DESC, created_at ASC",
            (contest_id,),
        )

    async def submissions_page(self, contest_id: int, page: int, per_page: int) -> tuple:
        r = await self.fetchone("SELECT COUNT(*) c FROM submissions WHERE contest_id=?", (contest_id,))
        total = r["c"] if r else 0
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = max(0, min(page, total_pages - 1))
        rows = await self.fetchall(
            "SELECT * FROM submissions WHERE contest_id=? ORDER BY likes_count DESC, created_at ASC "
            "LIMIT ? OFFSET ?",
            (contest_id, per_page, page * per_page),
        )
        return rows, total_pages, page

    async def like_submission(self, submission_id: int, liker_id: int) -> bool:
        existing = await self.fetchone(
            "SELECT 1 FROM submission_likes WHERE submission_id=? AND liker_id=?",
            (submission_id, liker_id),
        )
        if existing:
            return False
        await self.execute(
            "INSERT INTO submission_likes (submission_id, liker_id, liked_at) VALUES (?,?,?)",
            (submission_id, liker_id, time.time()),
        )
        await self.execute(
            "UPDATE submissions SET likes_count = likes_count + 1 WHERE id=?", (submission_id,)
        )
        sub = await self.get_submission(submission_id)
        if sub:
            await self.execute(
                "UPDATE participants SET points = points + 1 WHERE contest_id=? AND user_id=?",
                (sub["contest_id"], sub["user_id"]),
            )
        return True

    # ══════════════════════════════════════════════════
    # SETTINGS (key-value)
    # ══════════════════════════════════════════════════
    async def get_setting(self, key: str, default: Any = None):
        r = await self.fetchone("SELECT value FROM settings WHERE key=?", (key,))
        return r["value"] if r else default

    async def set_setting(self, key: str, value: str):
        await self.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value))
        )
