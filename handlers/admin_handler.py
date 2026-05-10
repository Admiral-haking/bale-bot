"""
پنل مدیریت - مدیریت محصولات، سفارشات، کاربران
"""
import logging
import os
from datetime import datetime
from utils.bale_api import bot
from utils.database import Database
from utils.safir_api import safir
from config import SHOP_NAME, SUPER_ADMIN_ID, logger

logger = logging.getLogger("AdminHandler")


class AdminHandler:
    _bcast_states = {}
    _tracking_states = {}

    @staticmethod
    def handle(chat_id, user_id, data, cq_id, msg_id=None):
        if not Database.is_admin(user_id):
            bot.answer_callback_query(cq_id, "دسترسی غیرمجاز!", show_alert=True); return
        if data.startswith("admin_remove_"):
            AdminHandler.remove_admin_action(chat_id, user_id, data, cq_id, msg_id); return
        if data.startswith("ticket_close_"):
            AdminHandler.close_ticket_action(chat_id, user_id, data, cq_id, msg_id); return
        if data.startswith("view_order_"):
            AdminHandler.view_order_detail(chat_id, user_id, data, cq_id, msg_id); return
        if data.startswith("change_status_"):
            AdminHandler.change_order_status(chat_id, user_id, data, cq_id, msg_id); return
        if data.startswith("del_product_"):
            AdminHandler.delete_product_action(chat_id, user_id, data, cq_id, msg_id); return
        if data.startswith("tracking_"):
            AdminHandler.request_tracking_code(chat_id, user_id, data, cq_id, msg_id); return
        if data.startswith("notify_"):
            AdminHandler.notify_user(chat_id, user_id, data, cq_id, msg_id); return
        if data.startswith("bcast_"):
            AdminHandler.handle_broadcast_flow(chat_id, user_id, data, cq_id, msg_id); return
        
        actions = {
            "admin_panel": AdminHandler.admin_panel,
            "admin_stats": AdminHandler.show_stats,
            "admin_tickets": AdminHandler.show_tickets,
            "admin_users": AdminHandler.show_users,
            "admin_manage_admins": AdminHandler.manage_admins,
            "admin_broadcast": AdminHandler.broadcast_panel,
            "admin_safir": AdminHandler.safir_panel,
            "admin_channel": AdminHandler.channel_panel,
            "admin_orders": AdminHandler.show_orders,
            "admin_products": AdminHandler.show_products_panel,
            "admin_groups": AdminHandler.show_groups_panel,
            "admin_close": AdminHandler.close_panel,
        }
        action = actions.get(data)
        if action: action(chat_id, user_id, cq_id, msg_id)
        else: bot.answer_callback_query(cq_id, "دستور ناشناخته")

    @staticmethod
    def admin_panel(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "پنل مدیریت")
        is_super = Database.is_super_admin(user_id)
        users = Database.get_user_count()
        orders = Database.get_orders_stats()['total']
        products = len(Database.get_products())
        tickets = len(Database.get_open_tickets())
        pending = Database.get_orders_stats()['pending']
        rows = [
            [{"text": f"آمار ({users} کاربر)", "callback_data": "admin_stats"}, {"text": f"سفارشات ({orders})", "callback_data": "admin_orders"}],
            [{"text": f"محصولات ({products})", "callback_data": "admin_products"}, {"text": f"تیکت‌ها ({tickets})", "callback_data": "admin_tickets"}],
            [{"text": "کاربران", "callback_data": "admin_users"}, {"text": "پیام همگانی", "callback_data": "admin_broadcast"}],
            [{"text": "سفیر", "callback_data": "admin_safir"}, {"text": "گروه و کانال", "callback_data": "admin_channel"}],
        ]
        if is_super: rows.append([{"text": "مدیریت ادمین‌ها", "callback_data": "admin_manage_admins"}])
        if pending > 0: rows.insert(0, [{"text": f"⚠️ {pending} سفارش در انتظار تایید!", "callback_data": "admin_orders"}])
        rows.append([{"text": "بستن", "callback_data": "admin_close"}])
        msg = f"پنل مدیریت\nمدیر: {user_id}"
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=bot.inline_keyboard(rows))
        else: bot.send_message(chat_id, msg, reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def show_stats(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "آمار")
        users = Database.get_user_count()
        tickets = len(Database.get_open_tickets())
        products = len(Database.get_products())
        admins = len(Database.get_all_admin_ids())
        stats = Database.get_orders_stats()
        groups_data = Database.get_all_groups_and_channels()
        total_groups = len(groups_data.get("groups",{})) + len(groups_data.get("channels",{}))
        msg = f"آمار فروشگاه\n\nکاربران: {users}\nسفارشات: {stats['total']} ({stats['pending']} در انتظار)\nمحصولات: {products}\nتیکت باز: {tickets}\nادمین‌ها: {admins}\nگروه/کانال: {total_groups}"
        kb = bot.inline_keyboard([[{"text":"بازخوانی","callback_data":"admin_stats"}],[{"text":"بازگشت","callback_data":"admin_panel"}]])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
        else: bot.send_message(chat_id, msg, reply_markup=kb)

    # ============================================================
    # مدیریت محصولات
    # ============================================================

    @staticmethod
    def show_products_panel(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "محصولات")
        products = Database.get_products()
        if not products:
            msg = "محصولی وجود ندارد.\n/addproduct برای افزودن"
            rows = [[{"text": "بازگشت", "callback_data": "admin_panel"}]]
        else:
            msg = f"مدیریت محصولات ({len(products)})\n\n"
            for p in products:
                msg += f"{p['id']} - {p['name']} - {p['price']}\n"
            rows = []
            for p in products[:5]:
                rows.append([{"text": f"حذف {p.get('id','?')} {p.get('name','')[:15]}", "callback_data": f"del_product_{p.get('id','?')}"}])
            rows.append([{"text": "➕ افزودن محصول جدید", "callback_data": "admin_add_product"}])
            rows.append([{"text": "بازگشت", "callback_data": "admin_panel"}])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg[:4000], reply_markup=bot.inline_keyboard(rows))
        else: bot.send_message(chat_id, msg[:4000], reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def delete_product_action(chat_id, user_id, data, cq_id, msg_id):
        pid = data.replace("del_product_", "")
        if Database.delete_product(pid):
            bot.answer_callback_query(cq_id, f"{pid} حذف شد")
            AdminHandler.show_products_panel(chat_id, user_id, cq_id, msg_id)
        else:
            bot.answer_callback_query(cq_id, "خطا", show_alert=True)

    # ============================================================
    # مدیریت سفارشات
    # ============================================================

    @staticmethod
    def show_orders(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "سفارشات")
        orders = Database.get_all_orders()
        if not orders:
            msg = "سفارشی وجود ندارد."
            rows = [[{"text": "بازگشت", "callback_data": "admin_panel"}]]
        else:
            status_icon = {"pending": "در انتظار", "confirmed": "تایید", "shipped": "ارسال", "delivered": "تحویل", "cancelled": "لغو"}
            sorted_o = sorted(orders.values(), key=lambda o: 0 if o.get('status')=='pending' else 1)
            msg = f"سفارشات ({len(orders)})\n\n"
            for o in sorted_o[:10]:
                items = ", ".join([i.get('name','')[:15] for i in o.get('items',[])])
                msg += f"{o.get('order_id', o.get('_id', '?'))} - {o.get('customer_name','ناشناس')}\n{items}\n{status_icon.get(o.get('status',''),'')}\nرهگیری: {o.get('tracking_code','-')}\n\n"
            rows = [[{"text":"بازخوانی","callback_data":"admin_orders"}],[{"text":"بازگشت","callback_data":"admin_panel"}]]
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg[:4000], reply_markup=bot.inline_keyboard(rows))
        else: bot.send_message(chat_id, msg[:4000], reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def view_order_detail(chat_id, user_id, data, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "جزئیات")
        oid = data.replace("view_order_", "")
        o = Database.get_order(oid)
        if not o: bot.send_message(chat_id, "یافت نشد."); return
        status_map = {"pending":"در انتظار","confirmed":"تایید","shipped":"ارسال","delivered":"تحویل","cancelled":"لغو"}
        items = "\n".join([f"- {i.get('name','')} x{i.get('quantity',1)}" for i in o.get('items',[])])
        msg = f"سفارش {oid}\nرهگیری: {o.get('tracking_code','-')}\nمشتری: {o.get('customer_name','')}\nتلفن: {o.get('customer_phone','')}\nآدرس: {o.get('customer_address','')}\nوضعیت: {status_map.get(o.get('status',''),'')}\nتاریخ: {o.get('created_at','')[:10]}\n\n{items}"
        rows = []
        st = o.get('status','')
        if st == 'pending':
            rows.append([{"text":"تایید","callback_data":f"change_status_{oid}_confirmed"},{"text":"لغو","callback_data":f"change_status_{oid}_cancelled"}])
        elif st == 'confirmed':
            rows.append([{"text":"ارسال شد","callback_data":f"change_status_{oid}_shipped"},{"text":"لغو","callback_data":f"change_status_{oid}_cancelled"}])
        elif st == 'shipped':
            rows.append([{"text":"تحویل شد","callback_data":f"change_status_{oid}_delivered"}])
        rows.append([{"text":"ثبت کد رهگیری","callback_data":f"tracking_{oid}"}])
        rows.append([{"text":"اطلاع به مشتری","callback_data":f"notify_{oid}"}])
        rows.append([{"text":"بازگشت","callback_data":"admin_orders"}])
        bot.send_message(chat_id, msg[:4000], reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def change_order_status(chat_id, user_id, data, cq_id, msg_id):
        parts = data.replace("change_status_", "").split("_", 1)
        if len(parts) != 2: bot.answer_callback_query(cq_id, "خطا", show_alert=True); return
        oid, st = parts[0], parts[1]
        o = Database.get_order(oid)
        status_map = {"pending":"در انتظار","confirmed":"تایید","shipped":"ارسال","delivered":"تحویل","cancelled":"لغو"}
        notify_map = {"confirmed":"تایید و در انتظار ارسال","shipped":"ارسال شد","delivered":"تحویل داده شد","cancelled":"لغو شد"}
        if Database.update_order_status(oid, st, by=str(user_id)):
            bot.answer_callback_query(cq_id, f"وضعیت: {status_map.get(st,st)}")
            if o and o.get('customer_id'):
                tracking = o.get('tracking_code', '')
                user_msg = f"به‌روزرسانی سفارش\n\nکد سفارش: {oid}\nکد رهگیری: {tracking}\nوضعیت جدید: {notify_map.get(st, st)}\n\nبرای پیگیری از /track استفاده کنید."
                try:
                    bot.send_message(o['customer_id'], user_msg)
                    bot.send_message(chat_id, "پیام به مشتری ارسال شد.")
                except: bot.send_message(chat_id, "خطا در ارسال به مشتری.")
        else: bot.answer_callback_query(cq_id, "خطا", show_alert=True)

    @staticmethod
    def request_tracking_code(chat_id, user_id, data, cq_id, msg_id):
        oid = data.replace("tracking_", "")
        o = Database.get_order(oid)
        if not o: bot.answer_callback_query(cq_id, "یافت نشد", show_alert=True); return
        AdminHandler._tracking_states[str(chat_id)] = oid
        bot.answer_callback_query(cq_id, "کد رهگیری را وارد کنید")
        kb = bot.inline_keyboard([[{"text":"لغو","callback_data":f"view_order_{oid}"}]])
        bot.send_message(chat_id, f"کد رهگیری جدید برای {oid}\n(کد فعلی: {o.get('tracking_code','-')})\n\nکد جدید را وارد کنید:", reply_markup=kb)

    @staticmethod
    def receive_tracking_code(chat_id, user_id, text):
        oid = AdminHandler._tracking_states.pop(str(chat_id), None)
        if not oid: return False
        if not text or len(text.strip()) < 3:
            bot.send_message(chat_id, "کد معتبر نیست (حداقل ۳ حرف).")
            AdminHandler._tracking_states[str(chat_id)] = oid
            return True
        new_code = text.strip()
        if Database.update_tracking_code(oid, new_code):
            o = Database.get_order(oid)
            bot.send_message(chat_id, f"کد رهگیری برای {oid} ثبت شد: {new_code}")
            if o and o.get('customer_id'):
                try:
                    bot.send_message(o['customer_id'], f"کد رهگیری سفارش شما\n\nکد سفارش: {oid}\nکد رهگیری: {new_code}\n\n/track")
                    bot.send_message(chat_id, "پیام به مشتری ارسال شد.")
                except: bot.send_message(chat_id, "خطا در ارسال به مشتری.")
        else: bot.send_message(chat_id, "خطا در ثبت کد رهگیری.")
        return True

    @staticmethod
    def notify_user(chat_id, user_id, data, cq_id, msg_id):
        oid = data.replace("notify_", "")
        o = Database.get_order(oid)
        if not o: bot.answer_callback_query(cq_id, "یافت نشد", show_alert=True); return
        bot.answer_callback_query(cq_id, "ارسال شد")
        if o.get('customer_id'):
            status_map = {"pending":"در انتظار","confirmed":"تایید","shipped":"ارسال","delivered":"تحویل","cancelled":"لغو"}
            msg = f"اطلاعیه سفارش\n\nکد سفارش: {oid}\nکد رهگیری: {o.get('tracking_code','-')}\nوضعیت: {status_map.get(o.get('status',''),'')}\n\n/track"
            try:
                bot.send_message(o['customer_id'], msg)
                bot.send_message(chat_id, f"پیام به {o.get('customer_name','مشتری')} ارسال شد.")
            except: bot.send_message(chat_id, "خطا در ارسال پیام.")

    # ============================================================
    # پیام همگانی
    # ============================================================

    @staticmethod
    def broadcast_panel(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "پیام همگانی")
        users = Database.get_user_count()
        groups_data = Database.get_all_groups_and_channels()
        msg = f"پیام همگانی\n\nکاربران: {users}\nگروه‌ها: {len(groups_data.get('groups',{}))}\nکانال‌ها: {len(groups_data.get('channels',{}))}\n\nمقصد را انتخاب کنید:"
        kb = bot.inline_keyboard([
            [{"text": f"کاربران ({users})", "callback_data": "bcast_users"}],
            [{"text": f"گروه‌ها ({len(groups_data.get('groups',{}))})", "callback_data": "bcast_groups"}],
            [{"text": f"کانال‌ها ({len(groups_data.get('channels',{}))})", "callback_data": "bcast_channels"}],
            [{"text": "همه", "callback_data": "bcast_all"}],
            [{"text": "بازگشت", "callback_data": "admin_panel"}]
        ])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
        else: bot.send_message(chat_id, msg, reply_markup=kb)

    @staticmethod
    def handle_broadcast_flow(chat_id, user_id, data, cq_id, msg_id):
        target_map = {"bcast_users":"users","bcast_groups":"groups","bcast_channels":"channels","bcast_all":"all"}
        target_names = {"bcast_users":"کاربران","bcast_groups":"گروه‌ها","bcast_channels":"کانال‌ها","bcast_all":"همه"}
        target = target_map.get(data)
        if not target: bot.answer_callback_query(cq_id, "خطا"); return
        AdminHandler._bcast_states[str(chat_id)] = {"target": target}
        bot.answer_callback_query(cq_id, f"ارسال به {target_names[data]}")
        kb = bot.inline_keyboard([[{"text":"لغو","callback_data":"admin_broadcast"}]])
        msg = f"متن پیام را برای {target_names[data]} بنویسید:"
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
        else: bot.send_message(chat_id, msg, reply_markup=kb)

    @staticmethod
    def receive_broadcast_text(chat_id, user_id, text):
        state = AdminHandler._bcast_states.pop(str(chat_id), None)
        if not state: return False
        target = state["target"]
        full = text
        sent = failed = 0
        if target in ("users","all"):
            for uid in Database.get_all_chat_ids():
                if str(uid) != str(chat_id):
                    try:
                        if bot.send_message(str(uid), full).get("ok"): sent+=1
                        else: failed+=1
                    except: failed+=1
        if target in ("groups","all"):
            groups_data = Database.get_all_groups_and_channels()
            for gid in groups_data.get("groups", {}):
                try:
                    if bot.send_message(str(gid), full).get("ok"): sent+=1
                    else: failed+=1
                except: failed+=1
        if target in ("channels","all"):
            groups_data = Database.get_all_groups_and_channels()
            for cid in groups_data.get("channels", {}):
                try:
                    if bot.send_message(str(cid), full).get("ok"): sent+=1
                    else: failed+=1
                except: failed+=1
        bot.send_message(chat_id, f"نتیجه: {sent} موفق / {failed} ناموفق")
        logger.info(f"Broadcast: {target} by {user_id} - {sent}ok {failed}fail")
        return True

    # ============================================================
    # تیکت‌ها
    # ============================================================

    @staticmethod
    def show_tickets(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "تیکت‌ها")
        tickets = Database.get_open_tickets()
        if not tickets: msg = "تیکت بازی وجود ندارد."
        else:
            msg = f"تیکت‌های باز ({len(tickets)})\n\n"
            for t in tickets[:5]:
                last = t["messages"][-1]["text"][:50] if t["messages"] else ""
                name = Database.get_user_info(t.get("customer_id","")).get("first_name","ناشناس")
                msg += f"{t.get('ticket_id', t.get('_id', '?'))} - {name}\n{last}\n\n"
        kb = bot.inline_keyboard([[{"text":"بازخوانی","callback_data":"admin_tickets"}],[{"text":"بازگشت","callback_data":"admin_panel"}]])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg[:4000], reply_markup=kb)
        else: bot.send_message(chat_id, msg[:4000], reply_markup=kb)

    @staticmethod
    def close_ticket_action(chat_id, user_id, data, cq_id, msg_id):
        tid = data.replace("ticket_close_", "")
        if Database.close_ticket(tid):
            bot.answer_callback_query(cq_id, "بسته شد")
            AdminHandler.show_tickets(chat_id, user_id, cq_id, msg_id)
        else: bot.answer_callback_query(cq_id, "خطا", show_alert=True)

    # ============================================================
    # کاربران
    # ============================================================

    @staticmethod
    def show_users(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "کاربران")
        users = Database.get_all_users()
        msg = f"کاربران ({len(users)})\n\n"
        if users:
            sorted_u = sorted(users.values(), key=lambda x: x.get("last_seen",""), reverse=True)
            for i, u in enumerate(sorted_u[:15], 1):
                name = u.get("first_name","ناشناس"); cid = u.get("chat_id","?")
                last = (u.get("last_seen") or "")[5:16]
                orders = Database.get_user_orders_count(cid)
                msg += f"{i}. {name} ({cid}) - {orders} سفارش\n   آخرین: {last}\n"
            if len(sorted_u) > 15: msg += f"\n...و {len(sorted_u)-15} کاربر دیگر"
        kb = bot.inline_keyboard([[{"text":"بازخوانی","callback_data":"admin_users"}],[{"text":"بازگشت","callback_data":"admin_panel"}]])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg[:4000], reply_markup=kb)
        else: bot.send_message(chat_id, msg[:4000], reply_markup=kb)

    # ============================================================
    # مدیریت ادمین‌ها
    # ============================================================

    @staticmethod
    def manage_admins(chat_id, user_id, cq_id, msg_id):
        if not Database.is_super_admin(user_id): bot.answer_callback_query(cq_id, "دسترسی ندارید", show_alert=True); return
        bot.answer_callback_query(cq_id, "ادمین‌ها")
        admins = Database.get_admins_list()
        msg = f"مدیریت ادمین‌ها\nارشد: {SUPER_ADMIN_ID}\n\n"
        rows = []
        if admins:
            for a in admins: msg += f"- {a}\n"; rows.append([{"text":f"حذف {a}","callback_data":f"admin_remove_{a}"}])
        else: msg += "زیر ادمینی وجود ندارد.\n"
        msg += "\n/addadmin [userId]"
        rows.append([{"text":"بازگشت","callback_data":"admin_panel"}])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=bot.inline_keyboard(rows))
        else: bot.send_message(chat_id, msg, reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def remove_admin_action(chat_id, user_id, data, cq_id, msg_id):
        if not Database.is_super_admin(user_id): bot.answer_callback_query(cq_id, "دسترسی ندارید", show_alert=True); return
        tid = int(data.replace("admin_remove_",""))
        if tid == SUPER_ADMIN_ID: bot.answer_callback_query(cq_id, "نمی‌توانید", show_alert=True); return
        if Database.remove_admin(tid): bot.answer_callback_query(cq_id, f"{tid} حذف شد"); AdminHandler.manage_admins(chat_id, user_id, cq_id, msg_id)
        else: bot.answer_callback_query(cq_id, "خطا", show_alert=True)

    # ============================================================
    # گروه‌ها
    # ============================================================

    @staticmethod
    def show_groups_panel(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "گروه‌ها")
        try:
            data = Database.get_all_groups_and_channels()
            groups = data.get("groups",{})
            channels = data.get("channels",{})
            msg = "گروه‌ها و کانال‌ها\n\n"
            if groups:
                msg += f"گروه‌ها ({len(groups)}):\n"
                msg += "\n".join([f"- {g.get('title','?')}" for gid,g in list(groups.items())[:10]])
                msg += "\n"
            if channels:
                msg += f"\nکانال‌ها ({len(channels)}):\n"
                msg += "\n".join([f"- {c.get('title','?')}" for cid,c in list(channels.items())[:10]])
                msg += "\n"
            if not groups and not channels:
                msg += "موردی ثبت نشده.\nربات را به گروه اضافه کنید."
        except Exception as e:
            msg = f"خطا در دریافت اطلاعات: {e}"
        kb = bot.inline_keyboard([[{"text":"بازگشت","callback_data":"admin_panel"}]])
        if msg_id:
            bot.edit_message_text(chat_id, msg_id, msg[:4000], reply_markup=kb)
        else:
            bot.send_message(chat_id, msg[:4000], reply_markup=kb)

    @staticmethod
    def close_panel(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "بسته شد")
        if msg_id: bot.delete_message(chat_id, msg_id)

    @staticmethod
    def safir_panel(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "سفیر")
        st = "فعال" if safir.validate_config() else "غیرفعال"
        kb = bot.inline_keyboard([[{"text":"بازگشت","callback_data":"admin_panel"}]])
        if msg_id: bot.edit_message_text(chat_id, msg_id, f"سفیر\nوضعیت: {st}", reply_markup=kb)
        else: bot.send_message(chat_id, f"سفیر\nوضعیت: {st}", reply_markup=kb)

    @staticmethod
    def channel_panel(chat_id, user_id, cq_id, msg_id):
        bot.answer_callback_query(cq_id, "گروه و کانال")
        msg = "مدیریت گروه و کانال"
        kb = bot.inline_keyboard([
            [{"text":"لیست","callback_data":"channel_list"},{"text":"اطلاعات","callback_data":"channel_info"}],
            [{"text":"اعضا","callback_data":"channel_members"},{"text":"مدیران","callback_data":"channel_admins"}],
            [{"text":"بن","callback_data":"channel_ban"},{"text":"آنبن","callback_data":"channel_unban"}],
            [{"text":"لینک","callback_data":"channel_invite"},{"text":"خروج","callback_data":"channel_leave"}],
            [{"text":"پست","callback_data":"channel_post"},{"text":"نظرسنجی","callback_data":"channel_poll"}],
            [{"text":"بازگشت","callback_data":"admin_panel"}]
        ])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
        else: bot.send_message(chat_id, msg, reply_markup=kb)
