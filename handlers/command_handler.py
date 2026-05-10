"""
مدیریت دستورات - نسخه ساده و خوانا
"""
import logging
from utils.bale_api import bot
from utils.database import Database
from utils.safir_api import safir
from config import SHOP_NAME, SHOP_TAGLINE, SHOP_PHONE, SHOP_ADDRESS, SUPER_ADMIN_ID, MAX_PRODUCTS_PER_PAGE, SHOP_DESCRIPTION, logger

logger = logging.getLogger("CommandHandler")


class CommandHandler:

    @staticmethod
    def handle(chat_id, user_id, text, message_id=None):
        parts = text.strip().split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if chat_id and user_id:
            Database.register_user(chat_id, {"first_name": "", "username": ""})

        handlers = {
            "/start": CommandHandler.cmd_start,
            "/help": CommandHandler.cmd_help,
            "/store": CommandHandler.cmd_store,
            "/products": CommandHandler.cmd_products,
            "/search": CommandHandler.cmd_search,
            "/cart": CommandHandler.cmd_cart,
            "/order": CommandHandler.cmd_order,
            "/track": CommandHandler.cmd_track,
            "/support": CommandHandler.cmd_support,
            "/about": CommandHandler.cmd_about,
            "/contact": CommandHandler.cmd_contact,
            "/profile": CommandHandler.cmd_profile,
            "/id": CommandHandler.cmd_id,
            "/time": CommandHandler.cmd_time,
            # ادمین
            "/admin": CommandHandler.cmd_admin,
            "/stats": CommandHandler.cmd_stats,
            "/tickets": CommandHandler.cmd_tickets,
            "/broadcast": CommandHandler.cmd_broadcast,
            "/addadmin": CommandHandler.cmd_add_admin,
            "/removeadmin": CommandHandler.cmd_remove_admin,
            "/admins": CommandHandler.cmd_list_admins,
            "/addproduct": CommandHandler.cmd_addproduct,
            "/saveproduct": CommandHandler.cmd_saveproduct,
            "/deleteproduct": CommandHandler.cmd_deleteproduct,
            "/editproduct": CommandHandler.cmd_editproduct,
            "/productslist": CommandHandler.cmd_productslist,
            "/safir": CommandHandler.cmd_safir,
            "/safirpanel": CommandHandler.cmd_safir_panel,
            "/group": CommandHandler.cmd_group_panel,
            "/group_info": CommandHandler.cmd_group_info,
            "/group_stats": CommandHandler.cmd_group_stats,
            "/group_members": CommandHandler.cmd_group_members,
            "/group_admins": CommandHandler.cmd_group_admins,
            "/group_ban": CommandHandler.cmd_group_ban,
            "/group_unban": CommandHandler.cmd_group_unban,
            "/group_promote": CommandHandler.cmd_group_promote,
            "/group_invite": CommandHandler.cmd_group_invite,
            "/group_title": CommandHandler.cmd_group_title,
            "/group_pin": CommandHandler.cmd_group_pin,
            "/group_leave": CommandHandler.cmd_group_leave,
            "/channel_post": CommandHandler.cmd_channel_post,
            "/channel_poll": CommandHandler.cmd_channel_poll,
            "/chatid": CommandHandler.cmd_chatid,
            "/block": CommandHandler.cmd_block_user,
            "/unblock": CommandHandler.cmd_unblock_user,
            "/cleanup": CommandHandler.cmd_cleanup,
        }
        handler = handlers.get(command)
        if handler:
            handler(chat_id, user_id, args, message_id)
        else:
            bot.send_message(chat_id, f"دستور {command} شناخته نشد.\nبرای راهنما /help را بزنید.")

    # ============================================================
    # بخش عمومی
    # ============================================================

    @staticmethod
    def cmd_start(chat_id, user_id, args, msg_id):
        """صفحه خوش آمدگویی"""
        msg = f"سلام! به {SHOP_NAME} خوش آمدید💚\n\n{SHOP_TAGLINE}\n\n{SHOP_DESCRIPTION}.\n\n🌾 آموزش های کاربردی رایگان\n📢 کانال آموزش و اخبار: @tebahmadi13\n\n📦 ثبت سفارش:\n👤 @tebahmadi_admin\n\nاز منوی زیر انتخاب کنید:"
        
        kb = bot.inline_keyboard([
            [{"text": "فروشگاه", "callback_data": "shop_menu"}],
            [{"text": "پشتیبانی", "callback_data": "support_start"}, {"text": "درباره ما", "callback_data": "about_shop"}],
            [{"text": "تماس با ما", "callback_data": "contact_info"}, {"text": "پروفایل من", "callback_data": "my_profile"}]
        ])
        bot.send_message(chat_id, msg, reply_markup=kb)

        # دکمه های دائمی
        if Database.is_admin(user_id):
            keys = [["فروشگاه", "پشتیبانی"], ["درباره ما", "تماس با ما"], ["سبد خرید", "پنل مدیریت"]]
        else:
            keys = [["فروشگاه", "پشتیبانی"], ["درباره ما", "تماس با ما"], ["سبد خرید", "پروفایل من"]]
        bot.send_message(chat_id, "دکمه های دسترسی سریع:", reply_markup=bot.reply_keyboard(keys))

    @staticmethod
    def cmd_help(chat_id, user_id, args, msg_id):
        """راهنما"""
        msg = f"راهنمای {SHOP_NAME}\n\n"
        msg += "دستورات عمومی:\n"
        msg += "/start - شروع\n/store - فروشگاه\n/search نام - جستجو\n"
        msg += "/cart - سبد خرید\n/track - پیگیری سفارش\n"
        msg += "/profile - پروفایل من\n/support - پشتیبانی\n"
        msg += "/about - درباره ما\n/contact - تماس با ما\n/id - شناسه من\n"
        if Database.is_admin(user_id):
            msg += "\nدستورات ادمین:\n"
            msg += "/admin - پنل مدیریت\n/stats - آمار\n"
            msg += "/tickets - تیکت ها\n/broadcast - پیام همگانی\n"
            msg += "/addproduct - افزودن محصول\n"
            msg += "/block id - مسدود کاربر\n/cleanup - پاکسازی"
        kb = bot.inline_keyboard([
            [{"text": "فروشگاه", "callback_data": "shop_menu"}, {"text": "پشتیبانی", "callback_data": "support_start"}],
        ])
        if Database.is_admin(user_id):
            kb["inline_keyboard"].append([{"text": "پنل مدیریت", "callback_data": "admin_panel"}])
        bot.send_message(chat_id, msg, reply_markup=kb)

    @staticmethod
    def cmd_store(chat_id, user_id, args, msg_id):
        """فروشگاه"""
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
        
        bot.send_message(chat_id, "به فروشگاه خوش آمدید. یکی از گزینه ها را انتخاب کنید:", reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def cmd_products(chat_id, user_id, args, msg_id):
        """محصولات با صفحه بندی"""
        products = Database.get_products()
        if not products:
            bot.send_message(chat_id, "هیچ محصولی ثبت نشده است.")
            return
        
        page = 0
        if args and args[0].isdigit():
            page = int(args[0]) - 1
        
        total_pages = (len(products) + MAX_PRODUCTS_PER_PAGE - 1) // MAX_PRODUCTS_PER_PAGE
        page = max(0, min(page, total_pages - 1))
        start = page * MAX_PRODUCTS_PER_PAGE
        end = start + MAX_PRODUCTS_PER_PAGE
        page_products = products[start:end]
        
        msg = f"محصولات (صفحه {page+1} از {total_pages})\n\n"
        for p in page_products:
            msg += f"- {p.get('name', '')}\n  {p.get('price', '')}\n\n"
        
        rows = []
        nav = []
        if page > 0:
            nav.append({"text": "قبلی", "callback_data": f"prod_page_{page-1}"})
        if page < total_pages - 1:
            nav.append({"text": "بعدی", "callback_data": f"prod_page_{page+1}"})
        if nav:
            rows.append(nav)
        rows.append([{"text": "جستجو", "callback_data": "shop_search"}, {"text": "سبد خرید", "callback_data": "shop_cart"}])
        rows.append([{"text": "فروشگاه", "callback_data": "shop_menu"}])
        
        bot.send_message(chat_id, msg[:4000], reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def cmd_search(chat_id, user_id, args, msg_id):
        """جستجو"""
        if not args:
            bot.send_message(chat_id, "برای جستجو بنویسید:\n/search نام محصول\nمثال: /search روغن")
            return
        
        query = " ".join(args)
        results = Database.search_products(query)
        
        if not results:
            bot.send_message(chat_id, f"نتیجه ای برای '{query}' پیدا نشد.")
            return
        
        msg = f"نتایج جستجو برای '{query}' ({len(results)} مورد)\n\n"
        for p in results[:10]:
            msg += f"- {p.get('name', '')} | {p.get('price', '')}\n  {p.get('category', '')}\n\n"
        
        kb = bot.inline_keyboard([[{"text": "فروشگاه", "callback_data": "shop_menu"}]])
        bot.send_message(chat_id, msg[:4000], reply_markup=kb)

    @staticmethod
    def cmd_cart(chat_id, user_id, args, msg_id):
        """سبد خرید"""
        cart = Database.get_cart(user_id)
        if not cart:
            bot.send_message(chat_id, "سبد خرید شما خالی است.\nبرای خرید به فروشگاه بروید.", 
                           reply_markup=bot.inline_keyboard([[{"text": "فروشگاه", "callback_data": "shop_menu"}]]))
            return
        
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
        bot.send_message(chat_id, msg, reply_markup=kb)

    @staticmethod
    def cmd_order(chat_id, user_id, args, msg_id):
        bot.send_message(chat_id, "برای ثبت سفارش:\n۱. از فروشگاه محصول را انتخاب کنید\n۲. به سبد خرید اضافه کنید\n۳. از سبد خرید ثبت سفارش را بزنید")

    @staticmethod
    def cmd_track(chat_id, user_id, args, msg_id):
        """پیگیری سفارش با کد رهگیری"""
        if args:
            code = " ".join(args)
            order = Database.get_order_by_tracking(code)
            if not order:
                bot.send_message(chat_id, "سفارشی با کد رهگیری '" + code + "' یافت نشد.")
                return
            status_map = {"pending": "در انتظار", "confirmed": "تایید", "shipped": "ارسال", "delivered": "تحویل", "cancelled": "لغو"}
            items = chr(10).join(["- " + i.get('name','') + " x" + str(i.get('quantity',1)) for i in order.get('items',[])])
            updates = order.get('status_updates', [])
            history = chr(10).join([u['time'][:16] + " - " + status_map.get(u['to'],u['to']) for u in updates[-3:]])
            msg = "پیگیری سفارش\n\n"
            msg += "کد سفارش: " + str(order.get('order_id','')) + "\n"
            msg += "کد رهگیری: " + str(order.get('tracking_code','-')) + "\n"
            msg += "وضعیت: " + status_map.get(order.get('status',''),order.get('status','')) + "\n"
            msg += "مشتری: " + str(order.get('customer_name','')) + "\n\n"
            msg += "اقلام:\n" + items + "\n\n"
            if history: msg += "تاریخچه:\n" + history
            bot.send_message(chat_id, msg[:4000])
            return
        orders = Database.get_customer_orders(user_id)
        if not orders:
            bot.send_message(chat_id, "شما سفارشی ندارید.", reply_markup=bot.inline_keyboard([[{"text":"فروشگاه","callback_data":"shop_menu"}]]))
            return
        status_map = {"pending": "در انتظار", "confirmed": "تایید", "shipped": "ارسال", "delivered": "تحویل", "cancelled": "لغو"}
        msg = "سفارش های شما\n\n"
        msg += "برای جستجو با کد رهگیری:\n/track [کد رهگیری]\n\n"
        for o in orders[-5:]:
            items = ", ".join([i.get('name','')[:20] for i in o.get('items',[])])
            st = status_map.get(o.get('status','pending'), o.get('status','pending'))
            msg += str(o.get('order_id', o.get('_id', '?'))) + "\n" + items + "\nوضعیت: " + st + "\nرهگیری: " + str(o.get('tracking_code','-')) + "\nتاریخ: " + str(o.get('created_at','')[:10] if o.get('created_at') else '-') + "\n\n"
        bot.send_message(chat_id, msg[:4000])
    @staticmethod
    def cmd_support(chat_id, user_id, args, msg_id):
        """پشتیبانی"""
        keyboard = bot.inline_keyboard([
            [{"text": "شروع گفتگو", "callback_data": "support_start"}],
            [{"text": "تیکت های من", "callback_data": "support_my_tickets"}],
            [{"text": "صفحه اصلی", "callback_data": "back_home"}]
        ])
        NL = chr(10)
        msg = "پشتیبانی فروشگاه" + NL + NL
        msg += "زمان پاسخگویی: حداکثر ۲۴ ساعت" + NL + NL
        msg += "برای تماس مستقیم:" + NL
        msg += "👤 @tebahmadi_admin" + NL + NL
        msg += "یا پیام خود را بنویسید:"
        bot.send_message(chat_id, msg, reply_markup=keyboard)

    @staticmethod
    def cmd_about(chat_id, user_id, args, msg_id):
        """درباره ما"""
        msg = f"درباره {SHOP_NAME}\n\n{SHOP_DESCRIPTION}.\n\nتمام محصولات از روغن ها و عصاره های کاملا طبیعی🧴🧪\n\n🌾 آموزش های کاربردی رایگان\n📢 کانال: @tebahmadi13\n\n📦 ثبت سفارش:\n👤 @tebahmadi_admin"
        kb = bot.inline_keyboard([
            [{"text": "فروشگاه", "callback_data": "shop_menu"}],
            [{"text": "صفحه اصلی", "callback_data": "back_home"}]
        ])
        bot.send_message(chat_id, msg, reply_markup=kb)

    @staticmethod
    def cmd_contact(chat_id, user_id, args, msg_id):
        """تماس با ما"""
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
        bot.send_message(chat_id, msg, reply_markup=kb)

    @staticmethod
    def cmd_profile(chat_id, user_id, args, msg_id):
        """پروفایل"""
        user_info = Database.get_user_info(chat_id)
        orders = Database.get_customer_orders(user_id)
        cart = Database.get_cart(user_id)
        cart_count = sum(i.get('quantity', 1) for i in cart)
        
        msg = f"پروفایل شما\n\n"
        msg += f"شناسه: {user_id}\n"
        msg += f"نام: {user_info.get('first_name', 'ثبت نشده')}\n"
        msg += f"کاربری: @{user_info.get('username', 'ندارد')}\n"
        msg += f"تعداد سفارش: {len(orders)}\n"
        msg += f"سبد خرید: {cart_count} قلم"
        
        kb = bot.inline_keyboard([
            [{"text": "سفارش های من", "callback_data": "my_orders"}],
            [{"text": "سبد خرید", "callback_data": "shop_cart"}],
            [{"text": "فروشگاه", "callback_data": "shop_menu"}]
        ])
        bot.send_message(chat_id, msg, reply_markup=kb)

    @staticmethod
    def cmd_id(chat_id, user_id, args, msg_id):
        bot.send_message(chat_id, f"شناسه شما\n\nکاربر: {user_id}\nگفتگو: {chat_id}")

    @staticmethod
    def cmd_time(chat_id, user_id, args, msg_id):
        import datetime
        now = datetime.datetime.now()
        bot.send_message(chat_id, f"زمان سرور\n\n{now.strftime('%Y/%m/%d')}\n{now.strftime('%H:%M:%S')}")

    # ============================================================
    # بخش ادمین
    # ============================================================

    @staticmethod
    def cmd_tickets(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!")
            return
        AdminHandler.show_tickets(chat_id, user_id, None, None)

    @staticmethod
    def cmd_admin(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!")
            return
        is_super = Database.is_super_admin(user_id)
        rows = [
            [{"text": "آمار", "callback_data": "admin_stats"}, {"text": "سفارشات", "callback_data": "admin_orders"}],
            [{"text": "محصولات", "callback_data": "admin_products"}, {"text": "تیکت ها", "callback_data": "admin_tickets"}],
            [{"text": "کاربران", "callback_data": "admin_users"}, {"text": "پیام همگانی", "callback_data": "admin_broadcast"}],
            [{"text": "سرویس سفیر", "callback_data": "admin_safir"}, {"text": "گروه و کانال", "callback_data": "admin_channel"}],
        ]
        if is_super:
            rows.append([{"text": "مدیریت ادمین ها", "callback_data": "admin_manage_admins"}])
        rows.append([{"text": "بستن", "callback_data": "admin_close"}])
        bot.send_message(chat_id, f"پنل مدیریت {SHOP_NAME}", reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def cmd_stats(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        AdminHandler.show_stats(chat_id, user_id, None, None)

    @staticmethod
    def cmd_broadcast(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        if not args:
            bot.send_message(chat_id, f"پیام همگانی\n\n/broadcast متن پیام\n\nتعداد کاربران: {Database.get_user_count()}")
            return
        text = " ".join(args)
        msg = f"پیام همگانی\n\n{text}"
        users = Database.get_all_chat_ids()
        sent = failed = 0
        for uid in users:
            if str(uid) != str(chat_id):
                try:
                    if bot.send_message(str(uid), msg).get("ok"): sent += 1
                    else: failed += 1
                except: failed += 1
        bot.send_message(chat_id, f"نتیجه: {sent} موفق / {failed} ناموفق")

    @staticmethod
    def cmd_add_admin(chat_id, user_id, args, msg_id):
        if not Database.is_super_admin(user_id):
            bot.send_message(chat_id, "فقط ادمین ارشد!"); return
        if not args:
            bot.send_message(chat_id, "/addadmin [userId]"); return
        try:
            new_id = int(args[0])
            if Database.add_admin(new_id):
                bot.send_message(chat_id, f"کاربر {new_id} ادمین شد.")
                bot.send_message(str(new_id), f"شما ادمین {SHOP_NAME} شدید.\n/admin")
            else:
                bot.send_message(chat_id, f"{new_id} قبلا ادمین است.")
        except ValueError:
            bot.send_message(chat_id, "شناسه نامعتبر.")

    @staticmethod
    def cmd_remove_admin(chat_id, user_id, args, msg_id):
        if not Database.is_super_admin(user_id):
            bot.send_message(chat_id, "فقط ادمین ارشد!"); return
        if not args:
            bot.send_message(chat_id, "/removeadmin [userId]"); return
        try:
            target_id = int(args[0])
            if target_id == SUPER_ADMIN_ID:
                bot.send_message(chat_id, "نمی توانید ادمین ارشد را حذف کنید!"); return
            if Database.remove_admin(target_id):
                bot.send_message(chat_id, f"ادمین {target_id} حذف شد.")
            else:
                bot.send_message(chat_id, f"{target_id} ادمین نیست.")
        except ValueError:
            bot.send_message(chat_id, "شناسه نامعتبر.")

    @staticmethod
    def cmd_list_admins(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی ندارید."); return
        admins = Database.get_admins_list()
        msg = f"لیست ادمین ها\n\nارشد: {SUPER_ADMIN_ID}\n\n"
        if admins:
            for a in admins:
                msg += f"- {a}\n"
        else:
            msg += "زیر ادمینی وجود ندارد.\n"
        msg += f"\nتعداد: {len(admins) + 1}"
        bot.send_message(chat_id, msg)

    @staticmethod
    def cmd_block_user(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        if not args:
            bot.send_message(chat_id, "/block [user_id]"); return
        try:
            target = int(args[0])
            if Database.block_user(target):
                bot.send_message(chat_id, f"کاربر {target} مسدود شد.")
            else:
                bot.send_message(chat_id, f"کاربر {target} یافت نشد.")
        except ValueError:
            bot.send_message(chat_id, "شناسه نامعتبر.")

    @staticmethod
    def cmd_unblock_user(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        if not args:
            bot.send_message(chat_id, "/unblock [user_id]"); return
        try:
            target = int(args[0])
            if Database.unblock_user(target):
                bot.send_message(chat_id, f"مسدودیت {target} رفع شد.")
            else:
                bot.send_message(chat_id, f"کاربر {target} یافت نشد.")
        except ValueError:
            bot.send_message(chat_id, "شناسه نامعتبر.")

    @staticmethod
    def cmd_cleanup(chat_id, user_id, args, msg_id):
        if not Database.is_super_admin(user_id):
            bot.send_message(chat_id, "فقط ادمین ارشد!"); return
        cleaned = Database.cleanup_old_tickets(30)
        bot.send_message(chat_id, f"{cleaned} تیکت قدیمی پاک شد.")

    # ============================================================
    # مدیریت محصولات
    # ============================================================

    @staticmethod
    def cmd_addproduct(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        msg = "افزودن محصول جدید\n\nفرمت:\n/saveproduct نام|قیمت|توضیحات|دسته|موجودی\n\nمثال:\n/saveproduct روغن زیتون|۵۰۰۰۰|روغن زیتون طبیعی|روغن ها|موجود"
        bot.send_message(chat_id, msg)

    @staticmethod
    def cmd_saveproduct(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        if not args:
            bot.send_message(chat_id, "لطفا اطلاعات محصول را وارد کنید.\n/addproduct"); return
        text = " ".join(args)
        parts = text.split("|")
        if len(parts) < 3:
            bot.send_message(chat_id, "فرمت نادرست!\n/saveproduct نام|قیمت|توضیحات|دسته|موجودی"); return
        name = parts[0].strip()
        price = parts[1].strip()
        desc = parts[2].strip() if len(parts) > 2 else ""
        category = parts[3].strip() if len(parts) > 3 else "عمومی"
        stock = parts[4].strip() if len(parts) > 4 else "موجود"
        products = Database.get_products()
        nums = [int(p['id'].replace('p','')) for p in products if p['id'].startswith('p') and p['id'][1:].isdigit()]
        new_num = max(nums) + 1 if nums else 1
        product = {'id': f"p{new_num}", 'name': name, 'price': price, 'description': desc, 'stock': stock, 'category': category}
        if Database.add_product(product):
            bot.send_message(chat_id, f"محصول اضافه شد:\n{name}\nقیمت: {price}\nشناسه: p{new_num}")
        else:
            bot.send_message(chat_id, "خطا در ذخیره!")

    @staticmethod
    def cmd_deleteproduct(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        if not args:
            bot.send_message(chat_id, "/deleteproduct [شناسه]\nمثال: /deleteproduct p1"); return
        if Database.delete_product(args[0].strip()):
            bot.send_message(chat_id, f"محصول {args[0]} حذف شد.")
        else:
            bot.send_message(chat_id, f"محصول {args[0]} یافت نشد.")

    @staticmethod
    def cmd_editproduct(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        if len(args) < 3:
            bot.send_message(chat_id, "/editproduct [id] [فیلد] [مقدار]\nفیلدها: name, price, description, stock, category\nمثال: /editproduct p1 price ۶۰۰۰۰"); return
        pid, field, value = args[0], args[1].lower(), " ".join(args[2:])
        valid = {"name", "price", "description", "stock", "category"}
        if field not in valid:
            bot.send_message(chat_id, f"فیلدهای مجاز: {', '.join(valid)}"); return
        if Database.update_product(pid, {field: value}):
            bot.send_message(chat_id, f"محصول {pid} بروز شد.\n{field}: {value}")
        else:
            bot.send_message(chat_id, f"محصول {pid} یافت نشد.")

    @staticmethod
    def cmd_productslist(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        products = Database.get_products()
        if not products:
            bot.send_message(chat_id, "هیچ محصولی وجود ندارد."); return
        msg = "لیست محصولات\n\n"
        for p in products:
            stock = "" if p.get('stock', 'ناموجود') != 'ناموجود' else "(ناموجود)"
            msg += f"{p['id']} - {p['name']} - {p['price']} {stock}\n"
        msg += f"\nتعداد: {len(products)}"
        bot.send_message(chat_id, msg[:4000])

    # ============================================================
    # سفیر
    # ============================================================

    @staticmethod
    def cmd_safir(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        config_ok = safir.validate_config()
        if not args:
            st = "فعال" if config_ok else "غیرفعال"
            msg = f"سرویس سفیر - وضعیت: {st}\n\n/safir send [شماره] [متن]\n/safir otp [شماره] [کد]\n/safir bulk [شماره1,شماره2] [متن]"
            bot.send_message(chat_id, msg); return
        if args[0] == "status":
            msg = f"وضعیت: {'فعال' if config_ok else 'غیرفعال'}\n{'(پیکربندی نشده)' if not config_ok else ''}"
            bot.send_message(chat_id, msg); return
        if not config_ok:
            bot.send_message(chat_id, "سفیر پیکربندی نشده!"); return
        if args[0] == "send" and len(args) >= 3:
            try:
                r = safir.send_text(args[1], " ".join(args[2:]))
                bot.send_message(chat_id, f"ارسال شد.")
            except Exception as e:
                bot.send_message(chat_id, f"خطا: {e}")
        elif args[0] == "otp" and len(args) >= 3:
            try:
                safir.send_otp(args[1], args[2])
                bot.send_message(chat_id, f"رمز یکبار مصرف ارسال شد.")
            except Exception as e:
                bot.send_message(chat_id, f"خطا: {e}")
        elif args[0] == "bulk" and len(args) >= 3:
            phones = [p.strip() for p in args[1].split(",")]
            results = safir.send_bulk(phones, text=" ".join(args[2:]))
            success = sum(1 for r in results if r["success"])
            bot.send_message(chat_id, f"{success} از {len(phones)} پیام ارسال شد.")
        else:
            bot.send_message(chat_id, "دستور نادرست!")

    @staticmethod
    def cmd_safir_panel(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        st = "فعال" if safir.validate_config() else "غیرفعال"
        kb = bot.inline_keyboard([[{"text": "وضعیت", "callback_data": "safir_status"}],[{"text": "بازگشت", "callback_data": "admin_panel"}]])
        bot.send_message(chat_id, f"سرویس سفیر\nوضعیت: {st}", reply_markup=kb)

    # ============================================================
    # گروه و کانال
    # ============================================================

    @staticmethod
    def cmd_group_panel(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id):
            bot.send_message(chat_id, "دسترسی غیرمجاز!"); return
        msg = "مدیریت گروه و کانال\n\n/group_info [chat_id]\n/group_members [chat_id]\n/group_admins [chat_id]\n/group_ban [chat_id] [user_id]\n/group_unban [chat_id] [user_id]\n/group_invite [chat_id]\n/group_title [chat_id] [عنوان]\n/group_leave [chat_id]\n/channel_post [chat_id] [متن]"
        kb = bot.inline_keyboard([[{"text": "بازگشت", "callback_data": "admin_panel"}]])
        bot.send_message(chat_id, msg, reply_markup=kb)

    @staticmethod
    def cmd_group_info(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or not args: return
        r = bot.get_chat(args[0])
        if r.get("ok"):
            i = r["result"]
            bot.send_message(chat_id, f"اطلاعات گروه\nشناسه: {i.get('id','')}\nنام: {i.get('title','')}\nنوع: {i.get('type','')}\nاعضا: {i.get('members_count','?')}")
        else:
            bot.send_message(chat_id, f"خطا: {r.get('error')}")

    @staticmethod
    def cmd_group_stats(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or not args: return
        cnt = bot.get_chat_members_count(args[0])
        adm = bot.get_chat_administrators(args[0])
        bot.send_message(chat_id, f"گروه {args[0]}\nاعضا: {cnt.get('result','?') if cnt.get('ok') else '?'}\nمدیران: {len(adm.get('result',[])) if adm.get('ok') else '?'}")

    @staticmethod
    def cmd_group_members(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or not args: return
        r = bot.get_chat_members_count(args[0])
        bot.send_message(chat_id, f"تعداد اعضا: {r.get('result','?')}" if r.get("ok") else f"خطا: {r.get('error')}")

    @staticmethod
    def cmd_group_admins(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or not args: return
        r = bot.get_chat_administrators(args[0])
        if r.get("ok"):
            msg = f"مدیران ({len(r['result'])})\n\n"
            for a in r["result"]:
                u = a.get("user", {})
                msg += f"- {u.get('first_name','')} ({u.get('id','')})\n"
            bot.send_message(chat_id, msg[:4000])
        else:
            bot.send_message(chat_id, f"خطا: {r.get('error')}")

    @staticmethod
    def cmd_group_ban(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or len(args) < 2: return
        try:
            r = bot.ban_chat_member(args[0], int(args[1]))
            bot.send_message(chat_id, "کاربر بن شد." if r.get("ok") else f"خطا: {r.get('error')}")
        except: bot.send_message(chat_id, "شناسه نامعتبر.")

    @staticmethod
    def cmd_group_unban(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or len(args) < 2: return
        try:
            r = bot.unban_chat_member(args[0], int(args[1]))
            bot.send_message(chat_id, "آنبن شد." if r.get("ok") else f"خطا: {r.get('error')}")
        except: bot.send_message(chat_id, "شناسه نامعتبر.")

    @staticmethod
    def cmd_group_promote(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or len(args) < 2: return
        try:
            r = bot.promote_chat_member(args[0], int(args[1]), can_change_info=True, can_delete_messages=True, can_invite_users=True, can_restrict_members=True, can_pin_messages=True)
            bot.send_message(chat_id, "ارتقا یافت." if r.get("ok") else f"خطا: {r.get('error')}")
        except: bot.send_message(chat_id, "شناسه نامعتبر.")

    @staticmethod
    def cmd_group_invite(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or not args: return
        r = bot.export_chat_invite_link(args[0])
        if not r.get("ok"):
            r = bot.create_chat_invite_link(args[0])
        bot.send_message(chat_id, f"لینک دعوت:\n{r.get('result') if isinstance(r.get('result'),str) else r.get('result',{}).get('invite_link','خطا')}" if r.get("ok") else f"خطا: {r.get('error')}")

    @staticmethod
    def cmd_group_title(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or len(args) < 2: return
        r = bot.set_chat_title(args[0], " ".join(args[1:]))
        bot.send_message(chat_id, "عنوان تغییر کرد." if r.get("ok") else f"خطا: {r.get('error')}")

    @staticmethod
    def cmd_group_pin(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or len(args) < 2: return
        try:
            r = bot.pin_chat_message(args[0], int(args[1]))
            bot.send_message(chat_id, "پین شد." if r.get("ok") else f"خطا: {r.get('error')}")
        except: bot.send_message(chat_id, "شناسه نامعتبر.")

    @staticmethod
    def cmd_group_leave(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or not args: return
        r = bot.leave_chat(args[0])
        bot.send_message(chat_id, "ربات خارج شد." if r.get("ok") else f"خطا: {r.get('error')}")

    @staticmethod
    def cmd_channel_post(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or len(args) < 2: return
        r = bot.send_message(args[0], " ".join(args[1:]))
        bot.send_message(chat_id, "پست ارسال شد." if r.get("ok") else f"خطا: {r.get('error')}")

    @staticmethod
    def cmd_channel_poll(chat_id, user_id, args, msg_id):
        if not Database.is_admin(user_id) or len(args) < 2: return
        poll_data = " ".join(args[1:])
        parts = poll_data.split("|")
        if len(parts) < 3:
            bot.send_message(chat_id, "فرمت: سوال|گزینه1|گزینه2"); return
        r = bot.send_poll(args[0], parts[0].strip(), [p.strip() for p in parts[1:]])
        bot.send_message(chat_id, "نظرسنجی ارسال شد." if r.get("ok") else f"خطا: {r.get('error')}")

    @staticmethod
    def cmd_chatid(chat_id, user_id, args, msg_id):
        bot.send_message(chat_id, f"شناسه این گفتگو:\n{chat_id}")
