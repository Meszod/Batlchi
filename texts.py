# -*- coding: utf-8 -*-
"""Barcha matn shablonlari shu yerda — o'zgartirish kerak bo'lsa faqat shu faylni tahrirlang."""

WELCOME = (
    "👋 Assalomu alaykum, <b>{name}</b>!\n\n"
    "🎉 Bu bot orqali siz o'zingizning shaxsiy <b>Konkurs (Battle)</b>ingizni "
    "kanal yoki guruhingizda o'tkazishingiz mumkin!\n\n"
    "Quyidagi menyudan kerakli bo'limni tanlang 👇"
)

MAIN_MENU_USER = "🏠 <b>Asosiy menyu</b>"

HELP_TEXT = (
    "ℹ️ <b>Bot qanday ishlaydi?</b>\n\n"
    "1️⃣ <b>+ Konkurs qilish</b> tugmasini bosing\n"
    "2️⃣ Botni o'z kanal/guruhingizga <b>admin</b> qilib qo'shing\n"
    "3️⃣ Konkurs o'tkaziladigan kanal/guruhni botga yuboring\n"
    "4️⃣ Xohlasangiz homiy (sponsor) kanal(lar) qo'shing\n"
    "5️⃣ Xohlasangiz Boost link qo'shing\n"
    "6️⃣ Davomiylikni tanlang va konkursni boshlang!\n\n"
    "💎 <b>PRO</b> xizmati orqali 7 kundan ortiq konkurs o'tkazish va "
    "majburiy global kanallarsiz ishlashingiz mumkin."
)

# ── Konkurs shartlari (admin tomonidan /admin panelidan o'zgartiriladi) ─
DEFAULT_CONTEST_RULES = (
    "📄 <b>Konkurs shartlari</b>\n\n"
    "1️⃣ Konkursga faqat botda ro'yxatdan o'tgan va barcha majburiy kanallarga "
    "a'zo bo'lgan ishtirokchilar qatnasha oladi.\n"
    "2️⃣ Har bir konkursning o'z turi va shartlari bor — batafsil ma'lumot "
    "konkurs e'lonida ko'rsatiladi.\n"
    "3️⃣ G'olib(lar) konkurs turiga qarab (ovoz, ball, referal yoki qur'a) "
    "avtomatik aniqlanadi va e'lon qilinadi.\n"
    "4️⃣ Firibgarlik, soxta akkauntlar yoki qoidabuzarlik aniqlansa, ishtirokchi "
    "konkursdan chetlashtirilishi mumkin.\n"
    "5️⃣ Sovrin va uni topshirish shartlari konkurs egasi (kanal/guruh admini) "
    "tomonidan belgilanadi — savollar bo'lsa konkurs egasiga murojaat qiling."
)

ADMIN_RULES_PROMPT = (
    "📄 <b>Konkurs shartlari matnini yuboring:</b>\n"
    "(HTML formatlash mumkin: &lt;b&gt;, &lt;i&gt;, va h.k.)\n\n"
    "Bekor qilish uchun /cancel"
)
ADMIN_RULES_SAVED = "✅ Konkurs shartlari matni yangilandi."

# ── Konkurs yaratish sizardi ──────────────────────────
ASK_CAPTION = (
    "🖊 <b>Tanlov matnini yuboring.</b>\n\n"
    "Shuningdek, matn bilan birga rasm, video yoki GIF ham yuborishingiz mumkin — "
    "buning uchun rasm/video/GIFni pastiga (caption) matningizni yozib yuboring.\n\n"
    "❗️ Siz faqat bitta media fayldan foydalanishingiz mumkin.\n\n"
    "Agar maxsus matn/media qo'shmoqchi bo'lmasangiz, pastdagi tugmani bosing 👇"
)
CAPTION_MEDIA_NO_TEXT = "❗️ Iltimos, rasm/video/GIF ostiga (caption) matn ham yozing."
CAPTION_SAVED = "✅ Qabul qilindi — bu matn (va media) konkurs postida ishlatiladi."
CAPTION_SKIPPED = "⏭ O'tkazib yuborildi — standart post matni ishlatiladi."

ASK_TYPE = (
    "🎮 <b>Konkurs turini tanlang</b>\n\n"
    "🗳 <b>Ovoz to'plash</b> — ishtirokchilar ro'yxatdan o'tadi, boshqalar ularning "
    "ismiga bosib ovoz beradi. Eng ko'p ovoz olgan g'olib bo'ladi.\n\n"
    "⭐ <b>Stars Battle</b> — ishtirokchilar o'zlari harakat qilib ball yig'adi:\n"
    "   ⭐ Stars yuborish — +{stars_points} ball\n"
    "   👍 Postga reaksiya — +{reaction_points} ball\n"
    "   🚀 Boost qilish — +{boost_points} ball\n"
    "Eng ko'p ball yig'gan g'olib bo'ladi.\n\n"
    "👥 <b>Referal</b> — har bir ishtirokchi shaxsiy taklif havolasiga ega. "
    "Taklif qilingan odam konkursga qo'shilsa — taklif qilganga +{referral_points} ball. "
    "Eng ko'p do'st taklif qilgan g'olib bo'ladi.\n\n"
    "🎲 <b>Oddiy Random</b> — klassik lotereya. Ball yo'q, faqat qo'shiling — "
    "g'oliblar konkurs oxirida <b>tasodifiy</b> tanlanadi.\n\n"
    "📸 <b>Rasm/Video</b> — ishtirokchilar rasm yoki video yuboradi, boshqalar "
    "ularga ❤️ layk bosadi. Eng ko'p layk olgan ish g'olib bo'ladi."
)

ASK_CHAT = (
    "📺 <b>Kanal yoki guruhni tanlang</b>\n\n"
    "Konkurs o'tkaziladigan kanal yoki guruhdan istalgan xabarni shu yerga "
    "<b>forward (uzatib)</b> yuboring.\n\n"
    "⚠️ <b>DIQQAT:</b> Konkurs havolasi (link) albatta shu kanal/guruh ID sidan "
    "avtomatik olinadi — adashib ketmasligi uchun @username emas, aynan forward "
    "qilingan xabar orqali aniqlanadi.\n\n"
    "❗️ Botni oldindan o'sha kanal/guruhga <b>administrator</b> qilib qo'shib qo'ying."
)

CHAT_NOT_ADMIN = (
    "❌ Bot bu kanal/guruhda <b>administrator</b> emas!\n\n"
    "Iltimos botni avval admin qiling (xabarlarni o'chirish va a'zolarni ko'rish "
    "huquqi bilan), so'ng xabarni qaytadan forward qiling."
)

USER_NOT_CHAT_ADMIN = (
    "❌ Siz bu kanal/guruhda administrator emassiz!\n\n"
    "Faqat o'zingiz administrator bo'lgan kanal/guruhda konkurs o'tkaza olasiz."
)

CHAT_CONFIRMED = (
    "✅ Kanal/guruh aniqlandi: <b>{title}</b>\n\n"
    "📺 <b>Homiy (sponsor) kanal(lar)</b>\n\n"
    "Ishtirokchilar konkursga qo'shilishdan oldin obuna bo'lishi shart bo'lgan "
    "homiy kanal(lar)ni forward qiling (bir nechta bo'lishi mumkin, max {max_n} ta).\n\n"
    "Homiy kanalga ham botni admin qilib qo'ying (a'zolikni tekshirish uchun).\n\n"
    "Tugatgach pastdagi <b>✅ Tayyor</b> tugmasini bosing."
)

SPONSOR_ADDED = "✅ Homiy kanal qo'shildi: <b>{title}</b>\nYana qo'shasizmi yoki tayyormisiz?"

SPONSOR_NOT_ADMIN = (
    "❌ Bot bu kanalda administrator emas, shuning uchun a'zolikni tekshira olmaydi.\n"
    "Botni admin qiling yoki boshqa kanal yuboring."
)

ASK_BOOST = (
    "🚀 <b>Boost bonusi (ixtiyoriy)</b>\n\n"
    "Boost — bu <b>majburiy emas</b>! Kanalni Boost qilgan ishtirokchilarga "
    "qo'shimcha <b>+{points} ball</b> beriladi va bu ularning g'olib bo'lish "
    "ehtimolini oshiradi (chunki g'oliblar <b>ball reytingi</b> bo'yicha aniqlanadi).\n\n"
    "Agar shu bonusni yoqmoqchi bo'lsangiz — boost qilinadigan kanalni forward qiling.\n"
    "Kerak bo'lmasa — <b>❌ Kerak emas</b> tugmasini bosing."
)

BOOST_SET = "✅ Boost bonusi yoqildi: <b>{title}</b>\nBoost qilganlarga +{points} ball beriladi."

ASK_DURATION = (
    "⏰ <b>Davomiylik</b>\n\n"
    "Konkurs qancha vaqt davom etsin?\n\n"
    "🆓 Bepul foydalanuvchilar uchun maksimal: <b>7 kun</b>\n"
    "💎 PRO foydalanuvchilar cheklovsiz (max {pro_days} kun)"
)

DURATION_TOO_LONG_FREE = (
    "❌ Bepul foydalanuvchilar 7 kundan ortiq konkurs o'tkaza olmaydi!\n\n"
    "💎 Bu cheklovni olib tashlash uchun <b>PRO</b> xizmatini sotib oling."
)

ASK_WINNERS_COUNT = "🏆 <b>Nechta g'olib bo'ladi?</b>\n\nRaqamni tanlang:"

ASK_END_CONDITION = (
    "🏁 <b>Konkurs qachon tugaydi?</b>\n\n"
    "⏰ <b>Vaqt bo'yicha</b> — belgilangan muddat tugaganda avtomatik yakunlanadi.\n"
    "👥 <b>Ishtirokchilar soni bo'yicha</b> — belgilangan sonli odam qo'shilganda darhol yakunlanadi.\n"
    "🔀 <b>Ikkalasi ham</b> — qaysi biri birinchi bo'lsa, o'shanda yakunlanadi."
)

ASK_TARGET_COUNT = "👥 <b>Nechta ishtirokchi bo'lganda tugasin?</b>\n\nRaqamni tanlang yoki o'zingiz kiriting:"
TARGET_COUNT_INVALID = "❌ Faqat musbat butun son kiriting (masalan: 50)."

ASK_PUBLISH_TIMING = (
    "📅 <b>Konkursni qachon joylaymiz?</b>\n\n"
    "🚀 <b>Hozir</b> — tasdiqlashingiz bilan darhol kanalga joylanadi.\n"
    "⏰ <b>Vaqt belgilash</b> — kelajakdagi bir vaqtga rejalashtiring."
)

ASK_SCHEDULE_TIME = (
    "⏰ <b>Qachon joylansin?</b>\n\n"
    "Tayyor variantni tanlang yoki aniq sana-vaqt kiriting: <code>KK.OO.YYYY SS:DD</code>\n"
    "Masalan: <code>05.09.2026 18:00</code>\n\n"
    "🌍 Vaqt server vaqti (UTC) bo'yicha hisoblanadi."
)
SCHEDULE_TIME_INVALID = (
    "❌ Format noto'g'ri yoki vaqt o'tmishda. To'g'ri format: "
    "<code>05.09.2026 18:00</code> va u kelajakda bo'lishi kerak."
)
CONTEST_SCHEDULED_OWNER = (
    "🗓 <b>Konkursingiz rejalashtirildi!</b>\n\n📺 {title}\n⏰ Joylanadi: <b>{when}</b>\n\n"
    "Belgilangan vaqtda avtomatik kanalga joylanadi."
)

CONFIRM_SUMMARY_STARS = (
    "📋 <b>Konkurs xulosasi</b> (⭐ Stars Battle)\n\n"
    "📺 Kanal/guruh: <b>{title}</b>\n"
    "📢 Homiy kanallar: {sponsors}\n"
    "🚀 Boost bonusi: {boost}\n"
    "🏁 Tugash sharti: <b>{end_info}</b>\n"
    "📅 Joylash: <b>{publish_info}</b>\n"
    "🏆 G'oliblar soni: <b>{winners}</b> (eng ko'p ball to'plaganlar)\n"
    "🌍 Global majburiy kanallar: {global_ch}\n\n"
    "Hammasi to'g'rimi?"
)

CONFIRM_SUMMARY_VOTE = (
    "📋 <b>Konkurs xulosasi</b> (🗳 Ovoz to'plash)\n\n"
    "📺 Kanal/guruh: <b>{title}</b>\n"
    "📢 Homiy kanallar: {sponsors}\n"
    "🏁 Tugash sharti: <b>{end_info}</b>\n"
    "📅 Joylash: <b>{publish_info}</b>\n"
    "🏆 G'oliblar soni: <b>{winners}</b> (eng ko'p ovoz olganlar)\n"
    "🌍 Global majburiy kanallar: {global_ch}\n\n"
    "Hammasi to'g'rimi?"
)

CONFIRM_SUMMARY_REFERRAL = (
    "📋 <b>Konkurs xulosasi</b> (👥 Referal)\n\n"
    "📺 Kanal/guruh: <b>{title}</b>\n"
    "📢 Homiy kanallar: {sponsors}\n"
    "🏁 Tugash sharti: <b>{end_info}</b>\n"
    "📅 Joylash: <b>{publish_info}</b>\n"
    "🏆 G'oliblar soni: <b>{winners}</b> (eng ko'p do'st taklif qilganlar)\n"
    "🌍 Global majburiy kanallar: {global_ch}\n\n"
    "Hammasi to'g'rimi?"
)

CONFIRM_SUMMARY_RANDOM = (
    "📋 <b>Konkurs xulosasi</b> (🎲 Oddiy Random)\n\n"
    "📺 Kanal/guruh: <b>{title}</b>\n"
    "📢 Homiy kanallar: {sponsors}\n"
    "🏁 Tugash sharti: <b>{end_info}</b>\n"
    "📅 Joylash: <b>{publish_info}</b>\n"
    "🏆 G'oliblar soni: <b>{winners}</b> (tasodifiy tanlanadi)\n"
    "🌍 Global majburiy kanallar: {global_ch}\n\n"
    "Hammasi to'g'rimi?"
)

CONFIRM_SUMMARY_MEDIA = (
    "📋 <b>Konkurs xulosasi</b> (📸 Rasm/Video)\n\n"
    "📺 Kanal/guruh: <b>{title}</b>\n"
    "📢 Homiy kanallar: {sponsors}\n"
    "🏁 Tugash sharti: <b>{end_info}</b>\n"
    "📅 Joylash: <b>{publish_info}</b>\n"
    "🏆 G'oliblar soni: <b>{winners}</b> (eng ko'p layk olganlar)\n"
    "🌍 Global majburiy kanallar: {global_ch}\n\n"
    "Hammasi to'g'rimi?"
)

CONTEST_STARTED_OWNER = "✅ <b>Konkursingiz boshlandi!</b>\n\n📺 {title}\n⏰ {duration}\n\nKanalga post joylandi."

CONTEST_CANCELLED = "❌ Konkurs yaratish bekor qilindi."

CONTEST_POST_TEMPLATE = (
    "🎉 <b>KONKURS BOSHLANDI!</b> 🎉\n\n"
    "🏆 G'oliblar soni: <b>{winners}</b>\n"
    "⏰ Tugash vaqti: <b>{end_time}</b>\n"
    "👥 Ishtirokchilar: <b>{count}</b>\n\n"
    "{rules}\n"
    "{boost_line}\n\n"
    "🏆 G'oliblar <b>ball reytingi</b> bo'yicha aniqlanadi!\n"
    "Qatnashish uchun pastdagi tugmani bosing! 👇"
)

VOTE_POST_TEMPLATE = (
    "🗳 <b>OVOZ TO'PLASH KONKURSI!</b> 🗳\n\n"
    "🏆 G'oliblar soni: <b>{winners}</b>\n"
    "⏰ Tugash vaqti: <b>{end_time}</b>\n"
    "👥 Ishtirokchilar: <b>{count}</b>\n\n"
    "{rules}\n\n"
    "1️⃣ Avval <b>Konkursga qo'shilish</b> tugmasini bosing\n"
    "2️⃣ So'ng <b>Ovoz berish</b> orqali sevimli ishtirokchingizga ovoz bering\n"
    "🏆 Eng ko'p ovoz olgan g'olib bo'ladi!\n\n"
    "Pastdagi tugmalardan foydalaning 👇"
)

STARS_POST_TEMPLATE = (
    "⭐ <b>STARS BATTLE!</b> ⭐\n\n"
    "🏆 G'oliblar soni: <b>{winners}</b>\n"
    "⏰ Tugash vaqti: <b>{end_time}</b>\n"
    "👥 Ishtirokchilar: <b>{count}</b>\n\n"
    "{rules}\n\n"
    "🏆 <b>Ball qanday yig'iladi:</b>\n"
    "⭐ Stars yuborish — +{stars_points} ball\n"
    "👍 Postga reaksiya bosish — +{reaction_points} ball\n"
    "🚀 Boost qilish — +{boost_points} ball\n\n"
    "Eng ko'p ball yig'gan g'olib bo'ladi!\n"
    "Qatnashish uchun pastdagi tugmani bosing 👇"
)

REFERRAL_POST_TEMPLATE = (
    "👥 <b>REFERAL KONKURSI!</b> 👥\n\n"
    "🏆 G'oliblar soni: <b>{winners}</b>\n"
    "⏰ Tugash vaqti: <b>{end_time}</b>\n"
    "👥 Ishtirokchilar: <b>{count}</b>\n\n"
    "{rules}\n\n"
    "1️⃣ Avval <b>Konkursga qo'shilish</b> tugmasini bosing\n"
    "2️⃣ So'ng <b>Taklif havolamni olish</b> orqali shaxsiy havolangizni oling\n"
    "3️⃣ Do'stlaringizga ulashing — har biri qo'shilsa +{referral_points} ball\n\n"
    "🏆 Eng ko'p do'st taklif qilgan g'olib bo'ladi!\n"
    "Qatnashish uchun pastdagi tugmani bosing 👇"
)

RANDOM_POST_TEMPLATE = (
    "🎲 <b>ODDIY RANDOM KONKURS!</b> 🎲\n\n"
    "🏆 G'oliblar soni: <b>{winners}</b>\n"
    "⏰ Tugash vaqti: <b>{end_time}</b>\n"
    "👥 Ishtirokchilar: <b>{count}</b>\n\n"
    "{rules}\n\n"
    "Hech qanday ball yoki ovoz kerak emas — shunchaki qo'shiling!\n"
    "🏆 G'oliblar konkurs oxirida <b>tasodifiy</b> tanlanadi.\n\n"
    "Qatnashish uchun pastdagi tugmani bosing 👇"
)

MEDIA_POST_TEMPLATE = (
    "📸 <b>RASM/VIDEO KONKURSI!</b> 📸\n\n"
    "🏆 G'oliblar soni: <b>{winners}</b>\n"
    "⏰ Tugash vaqti: <b>{end_time}</b>\n"
    "👥 Ishtirokchilar: <b>{count}</b>\n\n"
    "{rules}\n\n"
    "1️⃣ Avval <b>Konkursga qo'shilish</b> tugmasini bosing\n"
    "2️⃣ So'ng botga shaxsiy chatda 1 ta rasm yoki video yuboring\n"
    "3️⃣ Ishingiz shu yerga joylanadi, boshqalar ❤️ layk bosadi\n\n"
    "🏆 Eng ko'p layk olgan ish g'olib bo'ladi!\n"
    "Qatnashish uchun pastdagi tugmani bosing 👇"
)

RULES_LINE = "📌 Qatnashish sharti: pastdagi kanallarga obuna bo'lish"
BOOST_LINE = "🚀 Bonus: kanalni Boost qilsangiz +{points} ball olasiz (ixtiyoriy, majburiy emas!)"

JOIN_BUTTON = "🎉 Konkursga qo'shilish"
BOOST_BUTTON = "🚀 Boost qilib +{points} ball olish"
LEADERBOARD_BUTTON = "📊 Reyting"
VOTE_BUTTON = "🗳 Ovoz berish"
STARS_BUTTON = "⭐ Stars yuborish (+{points} ball)"

JOIN_SUCCESS = "✅ Siz konkursga muvaffaqiyatli qo'shildingiz! Omad tilaymiz 🍀"
JOIN_ALREADY = "ℹ️ Siz allaqachon qo'shilgansiz."
JOIN_BANNED = "🚫 Siz bloklangansiz, konkursda qatnasha olmaysiz."
JOIN_FINISHED = "⛔️ Bu konkurs allaqachon tugagan."

JOIN_MISSING_CHANNELS = (
    "❌ Qatnashish uchun quyidagi kanal(lar)ga obuna bo'ling, so'ng tugmani "
    "qaytadan bosing:\n\n{channels}"
)

BOOST_NOT_JOINED = "❌ Avval konkursga qo'shiling, so'ng boost qiling!"
BOOST_ALREADY = "ℹ️ Siz allaqachon boost uchun ball olgansiz!"
BOOST_NOT_DONE = "❌ Siz hali kanalni Boost qilmagansiz:\n🚀 {link}\n\nBoost qilib, qaytadan bosing."
BOOST_SUCCESS = "🎉 Rahmat! Sizga +{points} ball berildi!"

LEADERBOARD_EMPTY = "📊 Hozircha ishtirokchilar yo'q."
LEADERBOARD_HEADER = "📊 <b>Reyting (TOP {n})</b>\n\n"

# ── 🗳 Ovoz to'plash ─────────────────────────────────
VOTE_NOT_JOINED = "❌ Ovoz berish uchun avval konkursga qo'shiling."
VOTE_SELF = "❌ O'zingizga ovoz berolmaysiz!"
VOTE_NEW = "✅ Ovozingiz qabul qilindi!"
VOTE_CHANGED = "✅ Ovozingiz almashtirildi!"
VOTE_SAME = "ℹ️ Siz allaqachon shu ishtirokchiga ovoz bergansiz."
VOTE_LIST_HEADER = "🗳 <b>Kimga ovoz berasiz?</b>\n\nIsmni bosing — ovoz shunga beriladi:"
VOTE_LIST_EMPTY = "📭 Hozircha ishtirokchi yo'q."

# ── ⭐ Stars Battle ──────────────────────────────────
STARS_NOT_JOINED = "❌ Avval konkursga qo'shiling, so'ng Stars yuboring!"
STARS_INVOICE_TITLE = "⭐ Stars Battle — ovoz"
STARS_SUCCESS = "🎉 Rahmat! Sizga +{points} ball berildi!"

# ── 👥 Referal ────────────────────────────────────────
REFERRAL_BUTTON = "🔗 Taklif havolamni olish"
REFERRAL_NOT_JOINED = "❌ Avval konkursga qo'shiling, so'ng taklif havolangizni oling!"
REFERRAL_LINK_TEXT = (
    "🔗 <b>Sizning shaxsiy taklif havolangiz:</b>\n\n<code>{link}</code>\n\n"
    "Bu havolani do'stlaringizga ulashing. Har bir do'stingiz shu havola orqali "
    "botga kirib, keyin konkursga qo'shilsa — sizga <b>+{points} ball</b> beriladi.\n\n"
    "📊 Hozirgi taklif qilganlaringiz: <b>{count} kishi</b>"
)
REFERRAL_WELCOME_NUDGE = (
    "👋 Siz {name} tomonidan taklif qilindingiz!\n\n"
    "Konkursga qo'shilib, taklif qilgan do'stingizga ball qo'shib qo'ying 🙌"
)
REFERRAL_CREDITED = "✅ Yangi do'stingiz konkursga qo'shildi! Sizga +{points} ball berildi 🎉"

# ── 🎲 Oddiy Random ──────────────────────────────────
# (alohida matn kerak emas — umumiy JOIN_* matnlar ishlatiladi)

# ── 📸 Rasm/Video ────────────────────────────────────
MEDIA_ASK_SUBMISSION = (
    "📸 Konkursga qo'shildingiz! Endi shu yerga (shaxsiy chatga) "
    "<b>1 ta rasm yoki video</b> yuboring — u konkurs kanaliga joylanadi."
)
MEDIA_ALREADY_SUBMITTED = "ℹ️ Siz allaqachon ish yuborgansiz. Har ishtirokchi faqat 1 marta yubora oladi."
MEDIA_SUBMISSION_ACCEPTED = "✅ Ishingiz qabul qilindi va kanalga joylandi! Endi boshqalar sizga layk bosishi mumkin 🍀"
MEDIA_SUBMISSION_REJECTED = "❌ Faqat rasm yoki video yuboring."
MEDIA_NOT_JOINED_FOR_SUBMIT = "❌ Avval konkursga qo'shiling, so'ng ish yuboring!"
MEDIA_LIKE_SUCCESS = "❤️ Layk qo'shildi!"
MEDIA_LIKE_ALREADY = "ℹ️ Siz bu ishga allaqachon layk bosgansiz."
MEDIA_LIKE_OWN = "❌ O'z ishingizga layk bosolmaysiz!"
MEDIA_CAPTION = "📸 Ishtirokchi: {name}\n❤️ Layklar: {likes}"

# ── PRO ──────────────────────────────────────────────
PRO_INFO = (
    "💎 <b>PRO Obuna</b>\n\n"
    "PRO xizmati bilan siz:\n"
    "✅ Konkursni <b>7 kundan ortiq</b> davom ettira olasiz\n"
    "✅ Global majburiy kanallarsiz konkurs o'tkaza olasiz\n"
    "✅ Cheksiz sponsor kanal qo'sha olasiz\n"
    "✅ Ustuvor qo'llab-quvvatlash\n\n"
    "Tarifni tanlang 👇"
)

PRO_ALREADY = "💎 Sizda PRO obuna faol!\n\n⏳ Tugash sanasi: <b>{until}</b>"

PRO_PURCHASED = "🎉 Tabriklaymiz! Siz <b>{days} kunlik PRO</b> obunani faollashtirdingiz!"

# ── Admin ──────────────────────────────────────────────
ADMIN_MAIN = "🔧 <b>Super Admin Panel</b>\n\nKerakli bo'limni tanlang:"
NO_PERMISSION = "❌ Sizda ruxsat yo'q!"
