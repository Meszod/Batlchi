# 🎉 BB_bot PRO — Konkurs (Battle) boti

Bu bot orqali **har qanday foydalanuvchi** o'zining Telegram kanali yoki guruhida
konkurs (battle) o'tkaza oladi — endi faqat admin emas!

> 🔐 **Xavfsizlik:** `BOT_TOKEN`, `ADMIN_IDS` va boshqa maxfiy qiymatlarni hech
> qachon `config.py` ichiga qattiq yozmang va GitHub'ga commit qilmang — faqat
> `.env` fayl orqali bering (`.gitignore`da allaqachon bor). Agar tasodifan
> tokenni ochiq joyga yozib qo'ysangiz, uni **@BotFather** orqali darhol
> revoke qiling va yangisini oling.

## 📂 Loyiha tuzilishi

```
BB_bot_pro/
├── main.py                    # Botni ishga tushiruvchi asosiy fayl
├── config.py                  # Barcha sozlamalar (.env orqali)
├── texts.py                   # O'zbek tilidagi barcha matnlar
├── keyboards.py                # Barcha inline/reply klaviaturalar
├── utils.py                    # Yordamchi funksiyalar (vaqt, a'zolik tekshiruvi)
├── requirements.txt
├── Procfile                    # Railway/Heroku uchun
├── .env.example                # Namuna konfiguratsiya fayli
├── database/
│   ├── __init__.py
│   └── db.py                   # SQLite (aiosqlite) — butun bot holati shu yerda
└── handlers/
    ├── __init__.py              # Barcha handlerlarni ro'yxatdan o'tkazadi
    ├── common.py                 # /start, yordam, asosiy menyu
    ├── contest_create.py         # "➕ Konkurs qilish" — to'liq wizard (sizard)
    ├── contest_join.py           # Qo'shilish tugmasi + monitoring (job_queue)
    ├── contest_manage.py         # "📋 Mening konkurslarim" — boshqarish, g'olib tanlash
    ├── admin_panel.py             # Super admin panel
    └── pro.py                     # PRO obuna (Telegram Stars orqali to'lov)
```

## ⚙️ O'rnatish

```bash
git clone <repo>
cd BB_bot_pro
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env faylini oching va BOT_TOKEN, ADMIN_IDS ni to'ldiring
python main.py
```

## 🚀 Asosiy funksiyalar

### 1. Foydalanuvchilar uchun konkurs yaratish
- **"➕ Konkurs qilish"** tugmasi orqali istalgan foydalanuvchi konkurs boshlay oladi.
- Avval **konkurs turi tanlanadi** (5 xil):
  - 🗳 **Ovoz to'plash** — ishtirokchilar ro'yxatdan o'tadi, boshqa foydalanuvchilar
    ularning ismiga (DM orqali ochiladigan ro'yxatda) bosib ovoz beradi. Har bir
    odam butun konkurs davomida faqat **1 marta** ovoz bera oladi. Eng ko'p ovoz
    olgan g'olib bo'ladi.
  - ⭐ **Stars Battle** — ishtirokchilar o'zlari harakat qilib ball yig'adi:
    - ⭐ Stars yuborish (Telegram Stars orqali) — +{STARS_VOTE_POINTS} ball (necha marta ham qaytariladi)
    - 👍 Konkurs postiga reaksiya bosish — +{REACTION_POINTS} ball (bir marta)
    - 🚀 Kanalni Boost qilish — +{BOOST_POINTS} ball (bir marta, ixtiyoriy)
  - 👥 **Referal** — har bir ishtirokchi o'ziga xos taklif havolasiga ega
    (`t.me/<bot>?start=ref_<id>_<user_id>`). Taklif qilingan odam botni ishga
    tushirib, so'ng **konkursga qo'shilsa** (shart!) — taklif qilganga +ball.
    Eng ko'p do'st taklif qilgan g'olib bo'ladi.
  - 🎲 **Oddiy Random** — hech qanday ball/ovoz yo'q, faqat qo'shilish. G'oliblar
    konkurs oxirida `random.SystemRandom` bilan tasodifiy tanlanadi.
  - 📸 **Rasm/Video** — ishtirokchi shaxsiy chatda 1 ta rasm/video yuboradi, bot
    uni kanalga ❤️ layk tugmasi bilan joylaydi. Boshqalar layk bosadi, eng ko'p
    layk olgan g'olib bo'ladi.
- **🏁 Tugash sharti** (har bir konkurs uchun alohida tanlanadi):
  - ⏰ Vaqt bo'yicha — belgilangan muddat tugaganda.
  - 👥 Ishtirokchilar soni bo'yicha — masalan 50-kishi qo'shilgan zahoti (vaqtdan
    qat'i nazar, darhol) yakunlanadi.
  - 🔀 Ikkalasi ham — qaysi biri birinchi bo'lsa, o'shanda.
- **📅 Joylash vaqti**:
  - 🚀 Hozir — tasdiqlash bilan darhol kanalga joylanadi.
  - ⏰ Rejalashtirilgan — tayyor variant (1 soat/6 soat/ertaga) yoki aniq
    sana-vaqt (`05.09.2026 18:00`) kiritish orqali kelajakka belgilanadi; bot
    o'sha vaqtda avtomatik joylaydi (hatto bot restart bo'lsa ham — rejalashtirish
    bazada saqlanadi va tiklanadi).
- Keyingi bosqichlar (ikkala turda ham umumiy):
  1. Kanal/guruhdan xabar **forward** qilinadi → bot shu yerdan chat ID sini oladi
     (⚠️ **link emas, aynan chat ID orqali** — adashib ketmaslik uchun).
  2. Bot va foydalanuvchining o'sha yerda admin ekani tekshiriladi.
  3. Homiy (sponsor) kanal(lar) — bir nechtasi qo'shilishi mumkin.
  4. (Faqat Stars Battle) Boost bonusi (ixtiyoriy).
  5. Davomiylik tanlanadi, g'oliblar soni tanlanadi.
  6. Tasdiqlangach — bot avtomatik kanal/guruhga mos post joylaydi.

> ⚠️ **Muhim eslatma (reaksiya balli haqida):** Telegram Bot API kanallarda reaksiya
> qoldirgan foydalanuvchini ko'pincha **anonim** qilib yuboradi (ayniqsa kanal sozlamalarida
> "Anonim reaksiyalar" yoqilgan bo'lsa). Bunday holda bot muallifni aniqlay olmaydi va
> ball berilmaydi — bu Telegram platformasining o'zidagi cheklov, botning xatosi emas.
> Guruhlarda va aksariyat kanallarda muammosiz ishlaydi.


### 2. Global majburiy kanallar (faqat Super Admin)
- Super admin 1-2 ta **o'z reklama kanal(lar)i**ni belgilaydi.
- Bu kanallar PRO bo'lmagan har bir konkursga **avtomatik** homiy sifatida qo'shiladi.
- `/admin` → 🌍 Global kanallar.

### 3. PRO obuna
- **Telegram Stars (XTR)** orqali to'lov — tashqi merchant/provider token shart emas.
- PRO afzalliklari:
  - ✅ Konkursni 7 kundan ortiq davom ettirish.
  - ✅ Global majburiy kanallarsiz konkurs o'tkazish.
  - ✅ Cheksizga yaqin sponsor kanal.
- Tarif narxlari `config.py` dagi `PRO_PLANS` da sozlanadi.
- Admin PRO ni qo'lda ham berishi/olib tashlashi mumkin (`/admin` → 💎 PRO boshqaruvi).

### 4. Boost — ball tizimi (majburiy EMAS!)
- Boost qatnashish uchun **shart emas** — bu faqat bonus.
- Owner boost bonusini yoqsa, kanalni Boost qilgan ishtirokchilarga
  **+{BOOST_POINTS} ball** (default 15, `config.py` da sozlanadi) beriladi.
- **G'oliblar konkurs tugaganda ball reytingi bo'yicha avtomatik aniqlanadi**
  (eng ko'p ball to'plaganlar birinchi o'rinlarni oladi) — na admin qo'lda
  tanlashi, na tasodifiy lotereya kerak emas.
- "📊 Reyting" tugmasi orqali istalgan vaqt joriy holatni ko'rish mumkin.

### 5. Konkursni boshqarish
- **"📋 Mening konkurslarim"** — o'z konkurslaringizni ko'rish, to'xtatish, cho'zish,
  ishtirokchilarni ko'rish, g'oliblarni tanlash.
- Har bir konkurs uchun alohida monitoring `job` ishlaydi — bir nechta konkurs
  bir vaqtda parallel ishlaydi.
- Vaqt tugagach konkurs avtomatik yakunlanadi va egasiga xabar boradi.

### 6. Super Admin Panel (`/admin`)
- 🌍 Global majburiy kanallar
- 👥 Foydalanuvchilar (ban/unban/ogohlantirish/ma'lumot/TOP)
- 🔥 Barcha konkurslar
- 💎 PRO boshqaruvi
- 📊 Statistika
- 📢 Broadcast (barchaga xabar)

## 🔐 Xavfsizlik eslatmalari
- Har bir konkurs **faqat egasi** tomonidan boshqariladi (owner_id tekshiriladi).
- Konkurs kanal/guruh **ID orqali** saqlanadi, username emas — bu link almashtirilsa
  ham yoki kanal nomi o'zgarsa ham xatoliklarning oldini oladi.
- Bot ma'lumotlar bazasi SQLite (`data/bot.db`) da saqlanadi — restart bo'lganda
  hech narsa yo'qolmaydi, barcha faol konkurslar monitoring avtomatik tiklanadi.

## 🛠 Kengaytirish g'oyalari (keyingi qadamlar)
- Referal tizimi (do'st taklif qilib bonus olish)
- Konkurs shablonlarini saqlash (bir marta sozlab, keyin qayta ishlatish)
- Ko'p tilli interfeys (uz/ru/en)
- Web-панель (admin uchun tashqi dashboard)
- Click/Payme integratsiyasi (Stars o'rniga/qo'shimcha)

---
Savol yoki bug bo'lsa — kodni bemalol o'zgartiring, har bir fayl alohida va
mustaqil modul sifatida yozilgan 🚀
# Batlchi
