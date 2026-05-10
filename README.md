# 🤖 ربات فروشگاه طب احمدی - Bale Shop Bot

ربات فروشگاه آنلاین طب احمدی برای پیام‌رسان بله

## 🚀 نصب و اجرا

### پیش‌نیازها
- Python 3.8+
- کتابخانه‌های مورد نیاز: `pip install -r requirements.txt`

### تنظیمات
1. فایل `.env` را با توکن ربات خود پر کنید:
```
BALE_BOT_TOKEN=your_bot_token_here
SUPER_ADMIN_ID=your_bale_user_id
```

### اجرا
```bash
# حالت Long Polling (پیش‌فرض)
bash run.sh polling

# حالت Webhook
bash run.sh webhook 8443

# تست اتصال
bash run.sh test
```

## 📋 دستورات

### عمومی
| دستور | توضیح |
|-------|-------|
| `/start` | شروع و منوی اصلی |
| `/help` | راهنما |
| `/store` | فروشگاه |
| `/products` | محصولات |
| `/support` | پشتیبانی |
| `/about` | درباره ما |
| `/contact` | تماس با ما |
| `/id` | نمایش شناسه کاربری |
| `/time` | زمان سرور |

### مدیریت (فقط ادمین‌ها)
| دستور | توضیح |
|-------|-------|
| `/admin` | پنل مدیریت |
| `/stats` | آمار فروشگاه |
| `/broadcast [متن]` | پیام همگانی |
| `/tickets` | تیکت‌های پشتیبانی |
| `/addadmin [userId]` | افزودن ادمین |
| `/removeadmin [userId]` | حذف ادمین |
| `/admins` | لیست ادمین‌ها |
| `/addproduct` | راهنمای افزودن محصول |
| `/saveproduct [info]` | ذخیره محصول جدید |
| `/deleteproduct [id]` | حذف محصول |
| `/productslist` | لیست کامل محصولات |

## 📁 ساختار پروژه
```
bale-bot/
├── main.py                    # هسته اصلی ربات
├── webhook_server.py          # سرور وب‌هوک
├── config.py                  # تنظیمات
├── run.sh                     # اجراکننده
├── .env                       # متغیرهای محیطی
├── handlers/
│   ├── command_handler.py     # مدیریت دستورات
│   ├── callback_handler.py    # دکمه‌های شیشه‌ای
│   ├── message_handler.py     # مدیریت پیام‌ها
│   └── admin_handler.py       # پنل ادمین
├── utils/
│   ├── bale_api.py            # کتابخانه API بله
│   └── database.py            # دیتابیس JSON
├── data/                      # فایل‌های دیتابیس
└── logs/                      # لاگ‌ها
```

## ✨ ویژگی‌ها
- ✅ فروشگاه آنلاین با دکمه‌های شیشه‌ای
- ✅ سیستم تیکت پشتیبانی
- ✅ پنل مدیریت کامل
- ✅ پیام همگانی
- ✅ دیتابیس فایل JSON
- ✅ پشتیبانی از Long Polling و Webhook
