<div align="center">
  <img src="https://ble.ir/favicon.ico" alt="Bale Bot" width="80"/>
  <h1>🤖 Teb Ahmadi Bale Shop Bot</h1>
  <p><strong>ربات فروشگاه هوشمند طب احمدی برای پیام‌رسان بله</strong></p>
  <p>
    <em>Teb Ahmadi Smart Shop Bot for Bale Messenger</em>
  </p>
  
  <!-- Badges -->
  <p>
    <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python" alt="Python 3.8+"/>
    <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License"/>
    <img src="https://img.shields.io/badge/database-MongoDB-brightgreen?style=flat-square&logo=mongodb" alt="MongoDB"/>
    <img src="https://img.shields.io/badge/API-Bale%20Bot%20API-ff69b4?style=flat-square" alt="Bale Bot API"/>
    <img src="https://img.shields.io/badge/status-active-success?style=flat-square" alt="Active"/>
    <img src="https://img.shields.io/badge/maintained-yes-brightgreen?style=flat-square" alt="Maintained"/>
  </p>
</div>

---

## 📋 Table of Contents | فهرست مطالب

- [🇬🇧 English](#english)
- [🇮🇷 فارسی](#persian)

---

<a name="english"></a>
## 🌐 English

### 📖 Overview

**Teb Ahmadi Shop Bot** is a complete online store management bot for the [Bale Messenger](https://ble.ir) platform. It provides a full-featured shopping experience including product management, shopping cart, order tracking, support ticket system, and admin panel.

### ✨ Features

| Feature | Description |
|---------|-------------|
| 🛒 **Online Store** | Browse products by category with inline buttons |
| 🛍️ **Shopping Cart** | Add/remove items, checkout with order form |
| 📦 **Order Tracking** | Track orders with unique tracking codes |
| 🎫 **Ticket System** | Customer support with ticket management |
| 👑 **Admin Panel** | Complete management dashboard |
| 📢 **Broadcast** | Send bulk messages to users/groups/channels |
| 👥 **User Management** | Block/unblock users, view statistics |
| 🏷️ **Product Management** | Add/edit/delete products dynamically |
| 📊 **Statistics** | View sales, users, orders analytics |
| 🌐 **Safir Integration** | SMS sending via Safir API |
| 💬 **Persian UI** | Full Persian (Farsi) user interface |
| 🗄️ **MongoDB** | Reliable NoSQL database storage |

### 🚀 Quick Start

#### Prerequisites
- Python 3.8 or higher
- MongoDB server (local or remote)
- Bale Bot Token (from [@BaleBotFather](https://ble.ir/BaleBotFather))

#### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Admiral-haking/bale-bot.git
cd bale-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your bot token and settings

# 4. Run the bot
bash run.sh polling
```

#### Configuration (.env)

```env
# Required
BALE_BOT_TOKEN=your_bot_token_here
SUPER_ADMIN_ID=your_bale_user_id

# Optional
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=tebahmadi_bot
LOG_LEVEL=INFO
SAFIR_API_KEY=your_safir_api_key
SAFIR_BOT_ID=your_safir_bot_id
```

### 📁 Project Structure

```
bale-bot/
├── main.py                    # Bot core / Long Polling engine
├── webhook_server.py          # Webhook server (alternative mode)
├── config.py                  # Configuration & constants
├── run.sh                     # Startup script
├── deploy.sh                  # Deployment script
├── check_deps.sh              # Dependency checker
├── migrate_to_mongo.py        # JSON → MongoDB migration tool
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not in git)
├── .gitignore                 # Git ignore rules
├── handlers/
│   ├── __init__.py
│   ├── command_handler.py     # Command processing (/start, /help, etc.)
│   ├── callback_handler.py    # Inline button callbacks
│   ├── message_handler.py     # Text message handling
│   ├── admin_handler.py       # Admin panel & management
│   ├── channel_handler.py     # Group/channel management
│   └── order_handler.py       # Order processing workflow
├── utils/
│   ├── __init__.py
│   ├── bale_api.py            # Bale Bot API client library
│   ├── database.py            # MongoDB database layer (primary)
│   ├── mongo_db.py            # Alternative MongoDB class
│   └── safir_api.py           # Safir SMS API client
├── data/                      # Legacy JSON data directory
├── logs/                      # Application logs
└── .github/workflows/
    └── ci.yml                 # GitHub Actions CI/CD
```

### 🛠️ Commands

#### Public Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome screen & main menu |
| `/help` | Help guide |
| `/store` | Browse store |
| `/products [page]` | List products |
| `/search [query]` | Search products |
| `/cart` | View shopping cart |
| `/track [code]` | Track order |
| `/support` | Contact support |
| `/about` | About us |
| `/contact` | Contact information |
| `/profile` | View profile |
| `/id` | Show user/chat ID |
| `/time` | Server time |

#### Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Admin panel |
| `/stats` | Store statistics |
| `/tickets` | Support tickets |
| `/broadcast [text]` | Broadcast message |
| `/addadmin [userId]` | Add admin |
| `/removeadmin [userId]` | Remove admin |
| `/admins` | List admins |
| `/addproduct` | Add product guide |
| `/saveproduct [info]` | Save new product |
| `/deleteproduct [id]` | Delete product |
| `/editproduct [id] [field] [value]` | Edit product |
| `/productslist` | All products list |
| `/block [userId]` | Block user |
| `/unblock [userId]` | Unblock user |
| `/cleanup` | Clean old tickets |
| `/safir` | Safir SMS commands |

### 🗄️ Database

The bot uses **MongoDB** as its primary database. The data directory (`data/`) contains legacy JSON files for backup.

**Collections:**
- `users` — User profiles & activity
- `products` — Product catalog
- `orders` — Orders with tracking codes
- `tickets` — Support tickets
- `carts` — Shopping carts
- `admins` — Admin IDs
- `groups` — Saved groups
- `channels` — Saved channels
- `counters` — Auto-increment counters

### 🐳 Deployment

#### Using systemd (recommended)

```bash
# Install service
sudo cp bale-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bale-bot
sudo systemctl start bale-bot

# Check status
sudo systemctl status bale-bot

# View logs
journalctl -u bale-bot -f
```

#### Using PM2

```bash
npm install -g pm2
pm2 start main.py --interpreter python3 --name "bale-bot"
pm2 save
pm2 startup
```

### 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guidelines](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

### 📬 Contact

- **Admin:** @tebahmadi_admin (Bale)
- **Channel:** @tebahmadi13 (Bale)
- **GitHub:** [Admiral-haking](https://github.com/Admiral-haking)

---

<a name="persian"></a>
## 🇮🇷 فارسی

### 📖 معرفی

**ربات فروشگاه طب احمدی** یک ربات کامل مدیریت فروشگاه آنلاین برای پیام‌رسان [بله](https://ble.ir) است. این ربات تجربه خرید کاملی شامل مدیریت محصولات، سبد خرید، پیگیری سفارش، سیستم تیکت پشتیبانی و پنل مدیریت را فراهم می‌کند.

### ✨ ویژگی‌ها

| ویژگی | توضیحات |
|:-----:|:--------|
| 🛒 **فروشگاه آنلاین** | مرور محصولات به تفکیک دسته با دکمه‌های شیشه‌ای |
| 🛍️ **سبد خرید** | افزودن/حذف کالا، ثبت سفارش با فرم کامل |
| 📦 **پیگیری سفارش** | پیگیری با کد رهگیری یکتا |
| 🎫 **سیستم تیکت** | پشتیبانی مشتریان با مدیریت تیکت |
| 👑 **پنل مدیریت** | داشبورد کامل مدیریت |
| 📢 **پیام همگانی** | ارسال پیام گروهی به کاربران/گروه‌ها/کانال‌ها |
| 👥 **مدیریت کاربران** | مسدود/رفع مسدود کاربران، آمار بازدید |
| 🏷️ **مدیریت محصولات** | افزودن/ویرایش/حذف محصول به صورت پویا |
| 📊 **آمار** | آمار فروش، کاربران، سفارشات |
| 🌐 **سرویس سفیر** | ارسال پیامک از طریق API سفیر |
| 💬 **رابط کاربری فارسی** | رابط کاربری کاملاً فارسی |
| 🗄️ **پایگاه داده MongoDB** | ذخیره‌سازی مطمئن با دیتابیس NoSQL |

### 🚀 راه‌اندازی سریع

#### پیش‌نیازها
- پایتون ۳.۸ یا بالاتر
- سرور MongoDB (محلی یا راه دور)
- توکن ربات بله (از [@BaleBotFather](https://ble.ir/BaleBotFather))

#### نصب

```bash
# ۱. دریافت کدها
git clone https://github.com/Admiral-haking/bale-bot.git
cd bale-bot

# ۲. نصب وابستگی‌ها
pip install -r requirements.txt

# ۳. تنظیم محیط
cp .env.example .env
# ویرایش فایل .env با توکن ربات

# ۴. اجرای ربات
bash run.sh polling
```

#### تنظیمات (.env)

```env
# الزامی
BALE_BOT_TOKEN=your_bot_token_here
SUPER_ADMIN_ID=your_bale_user_id

# اختیاری
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=tebahmadi_bot
LOG_LEVEL=INFO
SAFIR_API_KEY=your_safir_api_key
SAFIR_BOT_ID=your_safir_bot_id
```

### 📁 ساختار پروژه

```
bale-bot/
├── main.py                    # هسته اصلی ربات / Long Polling
├── webhook_server.py          # سرور وب‌هوک (حالت جایگزین)
├── config.py                  # تنظیمات و ثابت‌ها
├── run.sh                     # اسکریپت اجرا
├── deploy.sh                  # اسکریپت استقرار
├── check_deps.sh              # بررسی وابستگی‌ها
├── migrate_to_mongo.py        # ابزار مهاجرت JSON → MongoDB
├── requirements.txt           # وابستگی‌های پایتون
├── .env                       # متغیرهای محیطی (در git نیست)
├── .gitignore                 # قوانین ignore گیت
├── handlers/
│   ├── __init__.py
│   ├── command_handler.py     # پردازش دستورات (/start, /help و ...)
│   ├── callback_handler.py    # پاسخ به دکمه‌های شیشه‌ای
│   ├── message_handler.py     # مدیریت پیام‌های متنی
│   ├── admin_handler.py       # پنل مدیریت
│   ├── channel_handler.py     # مدیریت گروه/کانال
│   └── order_handler.py       # پردازش سفارش
├── utils/
│   ├── __init__.py
│   ├── bale_api.py            # کتابخانه API بله
│   ├── database.py            # لایه دیتابیس MongoDB
│   ├── mongo_db.py            # کلاس جایگزین MongoDB
│   └── safir_api.py           # API سرویس سفیر
├── data/                      # دایرکتوری دیتا (قدیمی)
├── logs/                      # لاگ‌های برنامه
└── .github/workflows/
    └── ci.yml                 # پایپلاین CI/CD گیت‌هاب
```

### 🛠️ دستورات

#### دستورات عمومی

| دستور | توضیح |
|:-----:|:------|
| `/start` | صفحه خوش‌آمدگویی و منوی اصلی |
| `/help` | راهنما |
| `/store` | ورود به فروشگاه |
| `/products [صفحه]` | لیست محصولات |
| `/search [عبارت]` | جستجوی محصول |
| `/cart` | مشاهده سبد خرید |
| `/track [کد]` | پیگیری سفارش |
| `/support` | تماس با پشتیبانی |
| `/about` | درباره ما |
| `/contact` | اطلاعات تماس |
| `/profile` | مشاهده پروفایل |
| `/id` | نمایش شناسه کاربری |
| `/time` | زمان سرور |

#### دستورات مدیریت

| دستور | توضیح |
|:-----:|:------|
| `/admin` | پنل مدیریت |
| `/stats` | آمار فروشگاه |
| `/tickets` | تیکت‌های پشتیبانی |
| `/broadcast [متن]` | پیام همگانی |
| `/addadmin [userId]` | افزودن ادمین |
| `/removeadmin [userId]` | حذف ادمین |
| `/admins` | لیست ادمین‌ها |
| `/addproduct` | راهنمای افزودن محصول |
| `/saveproduct [اطلاعات]` | ذخیره محصول جدید |
| `/deleteproduct [شناسه]` | حذف محصول |
| `/editproduct [id] [فیلد] [مقدار]` | ویرایش محصول |
| `/productslist` | لیست کامل محصولات |
| `/block [userId]` | مسدود کاربر |
| `/unblock [userId]` | رفع مسدودیت |
| `/cleanup` | پاکسازی تیکت‌های قدیمی |
| `/safir` | دستورات سرویس سفیر |

### 🗄️ پایگاه داده

ربات از **MongoDB** به عنوان دیتابیس اصلی استفاده می‌کند. دایرکتوری `data/` حاوی فایل‌های JSON قدیمی برای پشتیبان است.

**کالکشن‌ها:**
- `users` — پروفایل و فعالیت کاربران
- `products` — کاتالوگ محصولات
- `orders` — سفارشات با کد رهگیری
- `tickets` — تیکت‌های پشتیبانی
- `carts` — سبدهای خرید
- `admins` — شناسه ادمین‌ها
- `groups` — گروه‌های ذخیره شده
- `channels` — کانال‌های ذخیره شده
- `counters` — شمارنده‌های خودکار

### 🐳 استقرار

#### با systemd (توصیه شده)

```bash
# نصب سرویس
sudo cp bale-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bale-bot
sudo systemctl start bale-bot

# بررسی وضعیت
sudo systemctl status bale-bot

# مشاهده لاگ
journalctl -u bale-bot -f
```

#### با PM2

```bash
npm install -g pm2
pm2 start main.py --interpreter python3 --name "bale-bot"
pm2 save
pm2 startup
```

### 🤝 مشارکت

از مشارکت شما استقبال می‌شود! لطفاً ابتدا [راهنمای مشارکت](CONTRIBUTING.md) را مطالعه کنید.

1. ریپازیتوری را Fork کنید
2. برنچ خود را ایجاد کنید (`git checkout -b feature/amazing-feature`)
3. تغییرات خود را Commit کنید (`git commit -m 'Add amazing feature'`)
4. به برنچ خود Push کنید (`git push origin feature/amazing-feature`)
5. یک Pull Request باز کنید

### 📄 مجوز

این پروژه تحت مجوز **MIT** منتشر شده است — برای جزئیات بیشتر فایل [LICENSE](LICENSE) را مشاهده کنید.

### 📬 تماس با ما

- **ادمین:** @tebahmadi_admin (بله)
- **کانال:** @tebahmadi13 (بله)
- **گیت‌هاب:** [Admiral-haking](https://github.com/Admiral-haking)

---

<div align="center">
  <p>Made with ❤️ for Teb Ahmadi | ساخته شده با ❤️ برای طب احمدی</p>
  <p>
    <sub>© 2025 Teb Ahmadi. All rights reserved.</sub>
  </p>
</div>

---

## 💡 Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Bot Framework** | python-telegram-bot | Mature library with async support and webhook mode |
| **Database** | SQLite | Lightweight, zero-config, sufficient for single-server deployment |
| **Deployment** | Polling + systemd | Simple, reliable, automatic restart on failure |
| **Language** | Python | Fast development, rich ecosystem for bot development |

## 🚀 Production Checklist

- [x] Automated deployment script
- [x] Error handling & retry logic
- [x] Logging system
- [x] Graceful shutdown
- [ ] Database backup
- [ ] Monitoring & alerting
- [ ] Load testing
