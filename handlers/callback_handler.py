"""
مدیریت دکمه ها - نسخه ساده و خوانا
"""
import logging
from utils.bale_api import bot
from utils.database import Database
from handlers.admin_handler import AdminHandler
from handlers.channel_handler import ChannelHandler
from handlers.message_handler import MessageHandler
from handlers.order_handler import OrderHandler
from utils.safir_api import safir
from config import SHOP_NAME, SHOP_TAGLINE, SHOP_PHONE, SHOP_ADDRESS, SHOP_DESCRIPTION, MAX_PRODUCTS_PER_PAGE, logger
logger = logging.getLogger("CallbackHandler")
class CallbackHandler:
    @staticmethod
    def handle(chat_id, user_id, data, cq_id, msg_id=None):
        logger.info(f"Callback {user_id}: {data}")
        if data.startswith("support_"):
            CallbackHandler.handle_support(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("bcast_"):
            AdminHandler.handle_broadcast_flow(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("admin_"):
            AdminHandler.handle(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("del_product_"):
            AdminHandler.handle(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("safir_"):
            CallbackHandler.handle_safir(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("channel_"):
            ChannelHandler.handle(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("reply_to_"):
            CallbackHandler.handle_admin_reply(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("ticket_"):
            AdminHandler.handle(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("order_"):
            CallbackHandler.handle_order(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("shop_"):
            CallbackHandler.handle_shop(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("prod_page_"):
            CallbackHandler.handle_product_page(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("add_cart_"):
            CallbackHandler.handle_add_to_cart(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("cart_"):
            CallbackHandler.handle_cart_actions(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("my_"):
            CallbackHandler.handle_my_panel(chat_id, user_id, data, cq_id, msg_id)
        elif data.startswith("del_cart_"):
            CallbackHandler.handle_remove_from_cart(chat_id, user_id, data, cq_id, msg_id)
        elif data == "about_shop":
            CallbackHandler.handle_info(chat_id, user_id, "about_shop", cq_id, msg_id)
        elif data == "contact_info":
            CallbackHandler.handle_info(chat_id, user_id, "contact_info", cq_id, msg_id)
        elif data == "back_home":
            CallbackHandler.handle_info(chat_id, user_id, "back_home", cq_id, msg_id)
        elif data.startswith("view_product_"):
            CallbackHandler.show_product_detail(chat_id, user_id, data, cq_id, msg_id)
        else:
            if cq_id and cq_id != "None" and str(cq_id).strip():
                bot.answer_callback_query(cq_id, "دستور ناشناخته")
    @staticmethod
    def handle_info(chat_id, user_id, data, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "باشه")
        if data == "about_shop":
            msg = f"درباره {SHOP_NAME}\n\n{SHOP_DESCRIPTION}\n\nتمام محصولات از روغن ها و عصاره های کاملا طبیعی🧴🧪\n\n🌾 آموزش های کاربردی رایگان\n📢 کانال: @tebahmadi13\n\n📦 ثبت سفارش:\n👤 @tebahmadi_admin"
            kb = bot.inline_keyboard([
                [{"text": "فروشگاه", "callback_data": "shop_menu"}],
                [{"text": "صفحه اصلی", "callback_data": "back_home"}]
            ])
        elif data == "contact_info":
            NL = chr(10)
            msg = "اطلاعات تماس" + NL + NL
            msg += "📦 ثبت سفارش:" + NL
            msg += "👤 @tebahmadi_admin" + NL + NL
            msg += "📢 کانال آموزش و اخبار:" + NL
            msg += "👥 @tebahmadi13" + NL + NL
            msg += "⏰ ساعت پاسخگویی: شنبه تا پنجشنبه ۹ تا ۲۰"

            kb = bot.inline_keyboard([
                [{"text": "پشتیبانی", "callback_data": "support_start"}],
                [{"text": "صفحه اصلی", "callback_data": "back_home"}]
            ])
        else:
            msg = f"{SHOP_NAME}\n\n{SHOP_TAGLINE}\n\n{SHOP_DESCRIPTION}\n\n🌾 آموزش های کاربردی رایگان\n📢 کانال: @tebahmadi13\n\n📦 ثبت سفارش:\n👤 @tebahmadi_admin\n\nیکی را انتخاب کنید:"
            kb = bot.inline_keyboard([
                [{"text": "فروشگاه", "callback_data": "shop_menu"}],
                [{"text": "پشتیبانی", "callback_data": "support_start"}, {"text": "درباره ما", "callback_data": "about_shop"}],
                [{"text": "تماس با ما", "callback_data": "contact_info"}, {"text": "پروفایل", "callback_data": "my_profile"}]
            ])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
        else: bot.send_message(chat_id, msg, reply_markup=kb)
    # ============================================================
    # فروشگاه
    # ============================================================
    @staticmethod
    def handle_shop(chat_id, user_id, data, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "باشه")
        if data == "shop_menu":
            products = Database.get_products()
            categories = Database.get_categories()
            rows = []
            if products:
                rows.append([{"text": f"همه محصولات ({len(products)})", "callback_data": "shop_all"}])
            for cat in categories[:4]:
                count = len(Database.get_products_by_category(cat))
                rows.append([{"text": f"{cat} ({count})", "callback_data": f"shop_cat_{cat}"}])
            rows.append([{"text": "جستجو", "callback_data": "shop_search"}, {"text": "سبد خرید", "callback_data": "shop_cart"}])
            rows.append([{"text": "پشتیبانی", "callback_data": "support_start"}])
            if msg_id: bot.edit_message_text(chat_id, msg_id, "فروشگاه. یکی را انتخاب کنید:", reply_markup=bot.inline_keyboard(rows))
            else: bot.send_message(chat_id, "فروشگاه. یکی را انتخاب کنید:", reply_markup=bot.inline_keyboard(rows))
        elif data == "shop_all":
            products = Database.get_products()
            if not products:
                bot.send_message(chat_id, "محصولی وجود ندارد."); return
            CallbackHandler._show_products_page(chat_id, msg_id, products, 0, "همه محصولات")
        elif data.startswith("shop_cat_"):
            cat = data.replace("shop_cat_", "")
            products = Database.get_products_by_category(cat)
            if not products:
                bot.send_message(chat_id, f"دسته {cat} خالی است."); return
            CallbackHandler._show_products_page(chat_id, msg_id, products, 0, cat)
        elif data == "shop_search":
            msg = "برای جستجو بنویسید:\n/search نام محصول\nمثال: /search روغن"
            kb = bot.inline_keyboard([[{"text": "فروشگاه", "callback_data": "shop_menu"}]])
            if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
            else: bot.send_message(chat_id, msg, reply_markup=kb)
        elif data == "shop_cart":
            CallbackHandler._show_cart(chat_id, user_id, msg_id)
    @staticmethod
    def _show_products_page(chat_id, msg_id, products, page, title):
        total_pages = (len(products) + MAX_PRODUCTS_PER_PAGE - 1) // MAX_PRODUCTS_PER_PAGE
        page = max(0, min(page, total_pages - 1))
        start = page * MAX_PRODUCTS_PER_PAGE
        end = start + MAX_PRODUCTS_PER_PAGE
        page_prods = products[start:end]
        msg = f"{title} (صفحه {page+1} از {total_pages})\n\n"
        for p in page_prods:
            msg += f"- {p.get('name', '')}\n  {p.get('price', '')}\n\n"
        rows = []
        for p in page_prods:
            rows.append([{"text": f"{p.get('name', '')[:20]} - {p.get('price', '')}", "callback_data": f"view_product_{p.get('id')}"}])
        nav = []
        if page > 0: nav.append({"text": "قبلی", "callback_data": f"prod_page_{page-1}"})
        if page < total_pages - 1: nav.append({"text": "بعدی", "callback_data": f"prod_page_{page+1}"})
        if nav: rows.append(nav)
        rows.append([{"text": "سبد خرید", "callback_data": "shop_cart"}, {"text": "فروشگاه", "callback_data": "shop_menu"}])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg[:4000], reply_markup=bot.inline_keyboard(rows))
        else: bot.send_message(chat_id, msg[:4000], reply_markup=bot.inline_keyboard(rows))
    @staticmethod
    def handle_product_page(chat_id, user_id, data, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "باشه")
        page = int(data.replace("prod_page_", ""))
        products = Database.get_products()
        CallbackHandler._show_products_page(chat_id, msg_id, products, page, "همه محصولات")
    @staticmethod
    def show_product_detail(chat_id, user_id, data, cq_id, msg_id):
        pid = data.replace("view_product_", "")
        product = Database.get_product(pid)
        if not product:
            bot.answer_callback_query(cq_id, "یافت نشد", show_alert=True); return
        bot.answer_callback_query(cq_id, product.get('name', ''))
        msg = f"{product.get('name', '')}\n\n"
        msg += f"قیمت: {product.get('price', 'نامشخص')}\n"
        msg += f"دسته: {product.get('category', 'عمومی')}\n"
        msg += f"توضیحات:\n{product.get('description', 'ندارد')}\n"
        msg += f"وضعیت: {product.get('stock', 'ناموجود')}\n"
        msg += f"شناسه: {pid}"
        kb = bot.inline_keyboard([
            [{"text": "افزودن به سبد خرید", "callback_data": f"add_cart_{pid}"}],
            [{"text": "سبد خرید", "callback_data": "shop_cart"}, {"text": "فروشگاه", "callback_data": "shop_menu"}]
        ])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
        else: bot.send_message(chat_id, msg, reply_markup=kb)
    # ============================================================
    # سبد خرید
    # ============================================================
    @staticmethod
    def handle_add_to_cart(chat_id, user_id, data, cq_id, msg_id):
        pid = data.replace("add_cart_", "")
        product = Database.get_product(pid)
        if not product:
            bot.answer_callback_query(cq_id, "خطا!", show_alert=True); return
        if Database.add_to_cart(user_id, pid):
            bot.answer_callback_query(cq_id, f"{product.get('name','')} به سبد اضافه شد.")
    @staticmethod
    def _show_cart(chat_id, user_id, msg_id):
        cart = Database.get_cart(user_id)
        if not cart:
            msg = "سبد خرید شما خالی است."
            kb = bot.inline_keyboard([[{"text": "فروشگاه", "callback_data": "shop_menu"}]])
        else:
            msg = "سبد خرید شما\n\n"
            total = 0
            for i, item in enumerate(cart, 1):
                msg += f"{i}. {item.get('name', '')} - {item.get('quantity', 1)} عدد\n"
                total += item.get('quantity', 1)
            msg += f"\nمجموع: {total} قلم"
            kb = bot.inline_keyboard([
                [{"text": "خالی کردن سبد", "callback_data": "cart_clear"}],
                [{"text": "ثبت سفارش", "callback_data": "cart_checkout"}],
                [{"text": "ادامه خرید", "callback_data": "shop_menu"}]
            ])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
        else: bot.send_message(chat_id, msg, reply_markup=kb)
    @staticmethod
    def handle_remove_from_cart(chat_id, user_id, data, cq_id, msg_id):
        pid = data.replace("del_cart_", "")
        bot.answer_callback_query(cq_id, "حذف شد")
        Database.remove_from_cart(user_id, pid)
        CallbackHandler._show_cart(chat_id, user_id, msg_id)
    @staticmethod
    def handle_cart_actions(chat_id, user_id, data, cq_id, msg_id):
        if data == "cart_clear":
            Database.clear_cart(user_id)
            bot.answer_callback_query(cq_id, "سبد خالی شد")
            if msg_id: bot.delete_message(chat_id, msg_id)
            bot.send_message(chat_id, "سبد خرید خالی شد.")
        elif data == "cart_checkout":
            cart = Database.get_cart(user_id)
            if not cart:
                bot.answer_callback_query(cq_id, "سبد خالی است!", show_alert=True); return
            bot.answer_callback_query(cq_id, "شروع ثبت سفارش")
            OrderHandler.start_order_from_cart(chat_id, user_id)
        else: bot.answer_callback_query(cq_id, "خطا")
    # ============================================================
    # پنل کاربری
    # ============================================================
    @staticmethod
    def handle_my_panel(chat_id, user_id, data, cq_id, msg_id):
        if data == "my_profile":
            bot.answer_callback_query(cq_id, "پروفایل")
            user_info = Database.get_user_info(chat_id)
            orders = Database.get_customer_orders(user_id)
            cart = Database.get_cart(user_id)
            cart_count = sum(i.get('quantity', 1) for i in cart)
            msg = f"پروفایل شما\n\n"
            msg += f"شناسه: {user_id}\n"
            msg += f"نام: {user_info.get('first_name', 'ثبت نشده')}\n"
            msg += f"کاربری: @{user_info.get('username', 'ندارد')}\n"
            msg += f"سفارش: {len(orders)} عدد\n"
            msg += f"سبد خرید: {cart_count} قلم"
            kb = bot.inline_keyboard([
                [{"text": "سفارش های من", "callback_data": "my_orders"}],
                [{"text": "سبد خرید", "callback_data": "shop_cart"}],
                [{"text": "فروشگاه", "callback_data": "shop_menu"}]
            ])
            if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
            else: bot.send_message(chat_id, msg, reply_markup=kb)
        elif data == "my_orders":
            bot.answer_callback_query(cq_id, "سفارش ها")
            orders = Database.get_customer_orders(user_id)
            if not orders:
                msg = "شما سفارشی ندارید."
            else:
                status_map = {"pending": "در انتظار", "confirmed": "تایید", "shipped": "ارسال", "delivered": "تحویل", "cancelled": "لغو"}
                msg = f"سفارش های شما ({len(orders)})\n\n"
                for o in orders[-5:]:
                    items = ", ".join([i.get('name','') for i in o.get('items',[])])
                    msg += f"{o.get('order_id', o.get('_id', '?'))}\n{items[:25]}\nوضعیت: {status_map.get(o['status'],o['status'])}\nتاریخ: {o.get('created_at','')[:10]}\n\n"
            kb = bot.inline_keyboard([
                [{"text": "پروفایل", "callback_data": "my_profile"}],
                [{"text": "فروشگاه", "callback_data": "shop_menu"}]
            ])
            if msg_id: bot.edit_message_text(chat_id, msg_id, msg[:4000], reply_markup=kb)
            else: bot.send_message(chat_id, msg[:4000], reply_markup=kb)
    # ============================================================
    # پشتیبانی
    # ============================================================
    @staticmethod
    def handle_support(chat_id, user_id, data, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "باشه")
        if data == "support_start":
            tickets = Database.get_customer_tickets(user_id)
            open_ticket = None
            for t in tickets:
                if t["status"] in ("open", "admin_replied"):
                    open_ticket = t; break
            if open_ticket:
                msg = f"شما یک تیکت باز دارید: {open_ticket.get('ticket_id', open_ticket.get('_id', '?'))}\nپیام خود را ارسال کنید."
            else:
                NL = chr(10)
                msg = "پشتیبانی فروشگاه" + NL + NL
                msg += "زمان پاسخگویی: حداکثر ۲۴ ساعت" + NL + NL
                msg += "برای تماس مستقیم:" + NL
                msg += "👤 @tebahmadi_admin" + NL + NL
                msg += "یا پیام خود را بنویسید:"
            kb = bot.inline_keyboard([
                [{"text": "تیکت های من", "callback_data": "support_my_tickets"}],
                [{"text": "صفحه اصلی", "callback_data": "back_home"}]
            ])
        elif data == "support_my_tickets":
            tickets = Database.get_customer_tickets(user_id)
            if not tickets:
                msg = "شما تیکتی ندارید."
            else:
                icons = {"open": "باز", "admin_replied": "پاسخ داده", "closed": "بسته"}
                msg = "تیکت های شما\n\n"
                for t in tickets[-5:]:
                    last = t["messages"][-1]["text"][:40] if t["messages"] else ""
                    msg += f"{t.get('ticket_id', t.get('_id', '?'))} - {icons.get(t['status'],t['status'])}\n{last}\n\n"
            kb = bot.inline_keyboard([
                [{"text": "شروع گفتگو", "callback_data": "support_start"}],
                [{"text": "صفحه اصلی", "callback_data": "back_home"}]
            ])
        else: return
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg[:4000], reply_markup=kb)
        else: bot.send_message(chat_id, msg[:4000], reply_markup=kb)
    # ============================================================
    # سفیر
    # ============================================================
    @staticmethod
    def handle_safir(chat_id, user_id, data, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "باشه")
        st = "فعال" if safir.validate_config() else "غیرفعال"
        msg = f"سرویس سفیر\nوضعیت: {st}"
        kb = bot.inline_keyboard([[{"text": "بازگشت", "callback_data": "admin_safir"}]])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
        else: bot.send_message(chat_id, msg, reply_markup=kb)
    # ============================================================
    # پاسخ ادمین
    # ============================================================
    @staticmethod
    def handle_admin_reply(chat_id, user_id, data, cq_id, msg_id):
        target_user_id = data.replace("reply_to_", "")
        MessageHandler.admin_waiting_for_reply[str(chat_id)] = target_user_id
        bot.answer_callback_query(cq_id, "پاسخ خود را بنویسید")
        kb = bot.inline_keyboard([[{"text": "لغو", "callback_data": "admin_tickets"}]])
        bot.send_message(chat_id, f"پاسخ به {target_user_id}\nمتن پاسخ را بنویسید:", reply_markup=kb)
    # ============================================================
    # سفارش
    # ============================================================
    @staticmethod
    def handle_order(chat_id, user_id, data, cq_id, msg_id):
        if data == "order_confirm":
            OrderHandler.confirm_order(chat_id, user_id)
            bot.answer_callback_query(cq_id, "سفارش ثبت شد")
        elif data == "order_cancel":
            OrderHandler.cancel_order(chat_id, user_id)
            bot.answer_callback_query(cq_id, "لغو شد")
        else: bot.answer_callback_query(cq_id, "خطا")