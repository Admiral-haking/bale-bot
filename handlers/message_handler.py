"""
مدیریت پیام ها - با پشتیبانی از کد رهگیری و اطلاع رسانی
"""
import logging
from utils.bale_api import bot
from utils.database import Database
from handlers.order_handler import OrderHandler
from handlers.admin_handler import AdminHandler
from handlers.channel_handler import admin_selected_chat
from config import SHOP_NAME, SHOP_PHONE, SHOP_ADDRESS, logger

logger = logging.getLogger("MessageHandler")


class MessageHandler:
    admin_waiting_for_reply = {}

    @staticmethod
    def handle(chat_id, user_id, message):
        user_info = message.get("from", {})
        Database.register_user(chat_id, {
            "first_name": user_info.get("first_name",""),
            "last_name": user_info.get("last_name",""),
            "username": user_info.get("username","")
        })
        text = message.get("text", "")

        # بررسی دریافت کد رهگیری از ادمین
        if AdminHandler._tracking_states.get(str(chat_id)):
            if AdminHandler.receive_tracking_code(chat_id, user_id, text):
                return

        # بررسی حالت broadcast
        if AdminHandler.receive_broadcast_text(chat_id, user_id, text): return

        # بررسی حالت کانال
        for prefix in ["ban_", "unban_", "promote_", "post_", "poll_", "title_", "pin_"]:
            key = prefix + str(user_id)
            if key in admin_selected_chat:
                target_chat = admin_selected_chat.pop(key)
                admin_selected_chat.pop(str(user_id), None)
                MessageHandler._handle_channel_action(chat_id, user_id, text, prefix, target_chat)
                return

        # بررسی پاسخ ادمین
        if str(chat_id) in MessageHandler.admin_waiting_for_reply:
            target_id = MessageHandler.admin_waiting_for_reply.pop(str(chat_id))
            MessageHandler.send_admin_reply(chat_id, user_id, target_id, text, message)
            return

        # بررسی حالت سفارش
        if OrderHandler.handle_message(chat_id, user_id, text): return

        # دکمه های کیبورد
        btn_map = {
            "فروشگاه": "shop_menu", "پشتیبانی": "support_start",
            "درباره ما": "about_shop", "تماس با ما": "contact_info",
            "سبد خرید": "shop_cart", "پروفایل من": "my_profile",
            "پنل مدیریت": "admin_panel",
        }
        if text in btn_map:
            cb = btn_map[text]
            if cb == "admin_panel":
                if Database.is_admin(user_id):
                    from handlers.command_handler import CommandHandler
                    CommandHandler.cmd_admin(chat_id, user_id, [], None)
                else: bot.send_message(chat_id, "دسترسی غیرمجاز!")
            else:
                from handlers.callback_handler import CallbackHandler
                CallbackHandler.handle(chat_id, user_id, cb, None, None)
            return

        # جستجوی خودکار
        if text and not text.startswith("/") and len(text) >= 2:
            results = Database.search_products(text)
            if results:
                msg = f"نتایج جستجو برای '{text}' ({len(results)} مورد)\n\n"
                for p in results[:5]:
                    msg += f"- {p.get('name', '')} | {p.get('price', '')}\n"
                kb = bot.inline_keyboard([[{"text": "فروشگاه", "callback_data": "shop_menu"}]])
                bot.send_message(chat_id, msg[:4000], reply_markup=kb)
                return

        # ادمین پیام عادی
        if Database.is_admin(user_id): return

        # کاربر معمولی -> تیکت
        MessageHandler.handle_customer_message(chat_id, user_id, text, message)

    @staticmethod
    def _handle_channel_action(chat_id, user_id, text, prefix, target_chat):
        try:
            if prefix in ("ban_", "unban_", "promote_"):
                uid = int(text.strip())
                if prefix == "ban_": r = bot.ban_chat_member(target_chat, uid)
                elif prefix == "unban_": r = bot.unban_chat_member(target_chat, uid)
                else: r = bot.promote_chat_member(target_chat, uid, can_change_info=True, can_delete_messages=True, can_invite_users=True, can_restrict_members=True, can_pin_messages=True)
                bot.send_message(chat_id, "انجام شد." if r.get("ok") else f"خطا: {r.get('error')}")
            elif prefix == "post_":
                r = bot.send_message(target_chat, text); bot.send_message(chat_id, "ارسال شد." if r.get("ok") else f"خطا: {r.get('error')}")
            elif prefix == "poll_":
                parts = text.split("|")
                if len(parts) >= 3:
                    r = bot.send_poll(target_chat, parts[0].strip(), [p.strip() for p in parts[1:]])
                    bot.send_message(chat_id, "نظرسنجی ارسال شد." if r.get("ok") else f"خطا: {r.get('error')}")
                else: bot.send_message(chat_id, "فرمت: سوال|گزینه1|گزینه2")
            elif prefix == "title_":
                r = bot.set_chat_title(target_chat, text.strip()); bot.send_message(chat_id, "عنوان تغییر کرد." if r.get("ok") else f"خطا: {r.get('error')}")
            elif prefix == "pin_":
                r = bot.pin_chat_message(target_chat, int(text.strip())); bot.send_message(chat_id, "پین شد." if r.get("ok") else f"خطا: {r.get('error')}")
        except ValueError: bot.send_message(chat_id, "شناسه نامعتبر!")
        except Exception as e: bot.send_message(chat_id, f"خطا: {str(e)}")

    @staticmethod
    def handle_customer_message(chat_id, user_id, text, message):
        existing = Database.get_customer_tickets(user_id)
        open_ticket = None
        for t in existing:
            if t["status"] in ("open", "admin_replied"): open_ticket = t; break
        if open_ticket:
            Database.add_to_ticket(open_ticket["id"], "customer", text, message.get("message_id"))
            bot.send_message(chat_id, "پیام شما به تیکت اضافه شد.")
            is_new = False
        elif text:
            ticket_id = Database.create_ticket(user_id, text, message.get("message_id"))
            if ticket_id:
                bot.send_message(chat_id, f"پیام شما دریافت شد.\nکد پیگیری: {ticket_id}\nحداکثر ۲۴ ساعت پاسخ می دهیم.")
                is_new = True
            else: bot.send_message(chat_id, "پیام شما دریافت شد."); return
        else: bot.send_message(chat_id, "پیام شما دریافت شد."); return

        admins = Database.get_all_admin_ids()
        name = message.get("from",{}).get("first_name","کاربر")
        info = f"پیام جدید از {name} ({user_id})\nتیکت: {ticket_id if is_new else open_ticket['id']}\n{(text or '[رسانه]')[:200]}"
        kb = bot.inline_keyboard([[{"text":"پاسخ","callback_data":f"reply_to_{user_id}"}],[{"text":"بستن","callback_data":f"ticket_close_{ticket_id}"}]])
        for admin_id in admins:
            if str(admin_id) != str(user_id):
                try: bot.send_message(str(admin_id), info, reply_markup=kb)
                except: pass

    @staticmethod
    def send_admin_reply(admin_chat_id, admin_id, target_user_id, text, message):
        if not text: bot.send_message(admin_chat_id, "متن را وارد کنید."); return
        result = bot.send_message(str(target_user_id), f"پاسخ پشتیبانی {SHOP_NAME}:\n\n{text}")
        if result.get("ok"):
            tickets = Database.get_customer_tickets(target_user_id)
            if tickets:
                open_t = [t for t in tickets if t["status"] != "closed"]
                if open_t: Database.add_to_ticket(open_t[-1]["id"], "admin", text)
            bot.send_message(admin_chat_id, f"پاسخ به {target_user_id} ارسال شد.")
        else: bot.send_message(admin_chat_id, f"خطا: {result.get('error')}")
