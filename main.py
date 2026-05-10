#!/usr/bin/env python3
"""
بازوی فروشگاه طب احمدی - Bale Shop Bot
ربات هوشمند فروشگاه آنلاین با قابلیت:
- مدیریت محصولات و سفارشات
- سیستم پشتیبانی و تیکتینگ
- پیام همگانی برای ادمین‌ها
- مدیریت داینامیک ادمین‌ها
- ارتباط مستقیم مشتری و ادمین
"""
import sys
import time
import signal
import threading
import os
from datetime import datetime

from config import BOT_TOKEN, logger, POLLING_TIMEOUT, POLLING_LIMIT, SHOP_NAME, DATA_DIR
from utils.bale_api import bot
from utils.database import Database
from handlers.command_handler import CommandHandler
from handlers.message_handler import MessageHandler
from handlers.callback_handler import CallbackHandler
from handlers.channel_handler import save_new_group


class BaleShopBot:
    """کلاس اصلی بازوی فروشگاه طب احمدی"""

    def __init__(self):
        self.running = False
        self.last_update_id = 0
        self.start_time = datetime.now()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.stats = {"updates_received": 0, "messages_sent": 0, "errors": 0, "commands_processed": 0}
        # استفاده از set با محدودیت ۱۰۰۰۰ و پاک کردن فقط قدیمی‌ها
        self.processed_ids = set()
        self.max_processed_ids = 10000
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info(f"Signal {signum} received. Shutting down...")
        self.running = False
        print("\n👋 بازو در حال خاموش شدن...")
        sys.exit(0)

    def check_token(self) -> bool:
        logger.info("🔑 Checking bot token...")
        result = bot.get_me()
        if result.get("ok"):
            bot_info = result["result"]
            logger.info(f"✅ Bot authenticated: @{bot_info.get('username', 'N/A')}")
            print(f"\n✅ *بازو با موفقیت متصل شد!*")
            print(f"🏪 فروشگاه: {SHOP_NAME}")
            print(f"🤖 نام: {bot_info.get('first_name', 'N/A')}")
            print(f"👤 یوزرنیم: @{bot_info.get('username', 'N/A')}")
            return True
        else:
            logger.error(f"❌ Invalid token: {result.get('error', 'Unknown error')}")
            print(f"\n❌ *خطا در اعتبارسنجی توکن!*")
            return False

    def _cleanup_processed_ids(self):
        """پاک کردن هوشمند update_idهای قدیمی برای جلوگیری از پردازش تکراری"""
        if len(self.processed_ids) > self.max_processed_ids:
            # نگه داشتن ۵۰۰۰ تای آخر
            sorted_ids = sorted(self.processed_ids)
            self.processed_ids = set(sorted_ids[-5000:])

    def _save_group_from_message(self, msg):
        """ذخیره خودکار گروه/کانال از روی پیام دریافتی - یکپارچه"""
        try:
            chat = msg.get("chat", {})
            ctype = chat.get("type", "")
            if ctype in ("group", "supergroup", "channel"):
                save_new_group(chat.get("id", ""), chat.get("title", "بدون نام"), ctype)
        except Exception as e:
            logger.debug(f"Group save error (non-critical): {e}")

    def process_update(self, update: dict):
        try:
            self.stats["updates_received"] += 1

            if "callback_query" in update:
                cq = update["callback_query"]
                cq_id = cq.get("id", "")
                user = cq.get("from", {})
                user_id = user.get("id", 0)
                chat_id = cq.get("message", {}).get("chat", {}).get("id", "")
                data = cq.get("data", "")
                message_id = cq.get("message", {}).get("message_id")
                logger.info(f"📞 CallbackQuery user={user_id} data={data}")
                
                # ذخیره کاربر
                Database.register_user(chat_id, {
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "username": user.get("username", "")
                })
                
                CallbackHandler.handle(str(chat_id), user_id, data, cq_id, message_id)
                return

            if "pre_checkout_query" in update:
                pcq = update["pre_checkout_query"]
                bot.answer_pre_checkout_query(pcq["id"], True)
                return

            if "message" in update or "edited_message" in update:
                msg = update.get("message") or update.get("edited_message")
                if not msg:
                    return

                # ذخیره خودکار گروه/کانال
                self._save_group_from_message(msg)

                chat = msg.get("chat", {})
                chat_id = chat.get("id", "")
                user = msg.get("from", {})
                user_id = user.get("id", 0)
                text = msg.get("text", "")
                msg_id = msg.get("message_id")

                if text and text.startswith("/"):
                    self.stats["commands_processed"] += 1
                    logger.info(f"⚡ Command '{text}' from user:{user_id}")
                    CommandHandler.handle(str(chat_id), user_id, text, msg_id)
                else:
                    logger.info(f"💬 Message from user:{user_id}")
                    MessageHandler.handle(str(chat_id), user_id, msg)

                self.stats["messages_sent"] += 1
                return

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Error processing update: {e}", exc_info=True)

    def run_polling(self):
        if not self.check_token():
            return
        self.running = True
        logger.info("🚀 Bot started with Long Polling...")

        print(f"""
╔══════════════════════════════════════════╗
║     🏪 {SHOP_NAME}         ║
║     بازوی هوشمند فروشگاه در بله           ║
╚══════════════════════════════════════════╝
        """)
        print("📡 روش: Long Polling")
        print(f"👥 کاربران: {Database.get_user_count()}")
        print(f"👑 ادمین‌ها: {len(Database.get_all_admin_ids())}")
        print("⏸ برای توقف: Ctrl+C\n")

        # حذف webhook در صورت وجود
        try:
            webhook_info = bot.get_webhook_info()
            if webhook_info.get("ok") and webhook_info["result"].get("url"):
                logger.info("🔄 Removing existing webhook...")
                bot.delete_webhook()
        except Exception as e:
            logger.warning(f"⚠️ Could not check/remove webhook: {e}")

        retry_count = 0
        max_retries = 10

        while self.running:
            try:
                result = bot.get_updates(offset=self.last_update_id, limit=POLLING_LIMIT, timeout=POLLING_TIMEOUT)
                if not result.get("ok"):
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(f"❌ Too many polling failures ({retry_count}). Restarting...")
                        time.sleep(10)
                        retry_count = 0
                    else:
                        time.sleep(2)
                    continue

                retry_count = 0  # موفقیت آمیز بود، ریست شمارنده
                updates = result.get("result", [])

                for update in updates:
                    if not self.running:
                        break

                    update_id = update.get("update_id", 0)

                    # جلوگیری از پردازش تکراری
                    if update_id < self.last_update_id or update_id in self.processed_ids:
                        continue

                    self.processed_ids.add(update_id)
                    self._cleanup_processed_ids()
                    self.process_update(update)

                    new_offset = update_id + 1
                    if new_offset > self.last_update_id:
                        self.last_update_id = new_offset

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"❌ Polling error: {e}", exc_info=True)
                time.sleep(3)

    def show_stats(self):
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"\n📊 *آمار نهایی {SHOP_NAME}*")
        print(f"⏱ زمان اجرا: {hours}h {minutes}m {seconds}s")
        print(f"📩 آپدیت‌ها: {self.stats['updates_received']}")
        print(f"👥 کاربران: {Database.get_user_count()}")
        print(f"❌ خطاها: {self.stats['errors']}")



def _ensure_data_files():
    """اطمینان از وجود فایل‌های دیتابیس"""
    import json
    files = {
        os.path.join(DATA_DIR, 'admins.json'): {"admins": []},
        os.path.join(DATA_DIR, 'users.json'): {"users": {}},
        os.path.join(DATA_DIR, 'products.json'): {"products": [], "categories": []},
        os.path.join(DATA_DIR, 'tickets.json'): {"tickets": {}, "counter": 0},
        os.path.join(DATA_DIR, 'orders.json'): {"orders": {}, "counter": 0},
        os.path.join(DATA_DIR, 'cart.json'): {"carts": {}},
        os.path.join(DATA_DIR, 'groups.json'): {"groups": {}, "channels": {}},
    }
    for path, default in files.items():
        if not os.path.exists(path):
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(default, f, ensure_ascii=False, indent=2)
                logger.info(f"📁 Created data file: {os.path.basename(path)}")
            except Exception as e:
                logger.error(f"❌ Failed to create {path}: {e}")

def main():
    print(f"\n🏪 {SHOP_NAME} - ربات هوشمند فروشگاه\n")

    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        print("❌ توکن بازو یافت نشد یا معتبر نیست!")
        print("⚠️  لطفاً توکن معتبر را در فایل .env قرار دهید:")
        print("   BALE_BOT_TOKEN=your_actual_token")
        sys.exit(1)

    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
    _ensure_data_files()

    bot_app = BaleShopBot()
    try:
        bot_app.run_polling()
    except KeyboardInterrupt:
        pass
    finally:
        bot_app.show_stats()


if __name__ == "__main__":
    main()
