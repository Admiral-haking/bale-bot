"""
مدیریت گروه و کانال - نسخه ساده
"""
import logging
from utils.bale_api import bot
from utils.database import Database
from config import SHOP_NAME, DATA_DIR, logger

logger = logging.getLogger("ChannelHandler")

admin_selected_chat = {}

def save_new_group(chat_id, title, chat_type):
    """ذخیره گروه/کانال در MongoDB"""
    try:
        Database.save_group(chat_id, title, chat_type)
    except Exception as e:
        logger.debug(f"Group save error (non-critical): {e}")

def get_saved_groups_list():
    data = Database.get_all_groups_and_channels()
    result = []
    for gid, g in data.get("groups",{}).items(): result.append({"id": gid, "title": g.get("title","بدون نام"), "type": "group"})
    for cid, c in data.get("channels",{}).items(): result.append({"id": cid, "title": c.get("title","بدون نام"), "type": "channel"})
    return result

class ChannelHandler:
    @staticmethod
    def handle(chat_id, user_id, data, cq_id, msg_id=None):
        if not Database.is_admin(user_id): bot.answer_callback_query(cq_id, "دسترسی غیرمجاز!", show_alert=True); return
        routes = {
            "channel_main": ChannelHandler.channel_main_menu, "channel_select": ChannelHandler.show_selection_list,
            "channel_info": ChannelHandler.show_chat_info, "channel_members": ChannelHandler.show_members,
            "channel_admins": ChannelHandler.show_admins, "channel_invite": ChannelHandler.make_invite_link,
            "channel_ban": ChannelHandler.ban_user_prompt, "channel_unban": ChannelHandler.unban_user_prompt,
            "channel_promote": ChannelHandler.promote_user_prompt, "channel_title": ChannelHandler.change_title_action,
            "channel_pin": ChannelHandler.pin_message_prompt, "channel_leave": ChannelHandler.leave_chat_action,
            "channel_post": ChannelHandler.post_to_channel_prompt, "channel_poll": ChannelHandler.poll_action,
        }
        if data in routes: routes[data](chat_id, user_id, cq_id, msg_id)
        elif data.startswith("pick_chat_"):
            picked = data.replace("pick_chat_",""); admin_selected_chat[str(user_id)] = picked
            bot.answer_callback_query(cq_id, "انتخاب شد"); ChannelHandler.channel_main_menu(chat_id, user_id, cq_id, msg_id)
        else: bot.answer_callback_query(cq_id, "ناشناخته")

    @staticmethod
    def channel_main_menu(chat_id, user_id, cq_id=None, msg_id=None):
        bot.answer_callback_query(cq_id, "مدیریت گروه")
        selected = admin_selected_chat.get(str(user_id))
        msg = "مدیریت گروه و کانال\n\n"
        if selected:
            data = Database.get_all_groups_and_channels()
            all_items = {**data.get("groups",{}), **data.get("channels",{})}
            info = all_items.get(selected,{})
            msg += f"انتخاب شده: {info.get('title',selected)}\nشناسه: {selected}\n\n"
        else: msg += "گروهی انتخاب نشده.\n\n"
        msg += "گزینه مورد نظر:"
        rows = [[{"text": "انتخاب گروه", "callback_data": "channel_select"}]]
        if selected:
            rows += [
                [{"text":"اطلاعات","callback_data":"channel_info"},{"text":"اعضا","callback_data":"channel_members"}],
                [{"text":"مدیران","callback_data":"channel_admins"},{"text":"لینک","callback_data":"channel_invite"}],
                [{"text":"بن","callback_data":"channel_ban"},{"text":"آنبن","callback_data":"channel_unban"}],
                [{"text":"ارتقا","callback_data":"channel_promote"},{"text":"عنوان","callback_data":"channel_title"}],
                [{"text":"پین","callback_data":"channel_pin"},{"text":"خروج","callback_data":"channel_leave"}],
                [{"text":"پست","callback_data":"channel_post"},{"text":"نظرسنجی","callback_data":"channel_poll"}],
            ]
        rows.append([{"text":"بازگشت","callback_data":"admin_panel"}])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=bot.inline_keyboard(rows))
        else: bot.send_message(chat_id, msg, reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def show_selection_list(chat_id, user_id, cq_id=None, msg_id=None):
        bot.answer_callback_query(cq_id, "لیست")
        items = get_saved_groups_list()
        if not items:
            msg = "گروهی ذخیره نشده.\nربات را به گروه اضافه کنید."
            rows = [[{"text":"بازگشت","callback_data":"channel_main"}]]
        else:
            msg = f"انتخاب کنید ({len(items)}):\n\n"
            rows = [[{"text": f"{'کانال' if i['type']=='channel' else 'گروه'} {i['title'][:20]}", "callback_data": f"pick_chat_{i['id']}"}] for i in items]
            rows.append([{"text":"بازگشت","callback_data":"channel_main"}])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=bot.inline_keyboard(rows))
        else: bot.send_message(chat_id, msg, reply_markup=bot.inline_keyboard(rows))

    @staticmethod
    def _req(user_id): return admin_selected_chat.get(str(user_id))

    @staticmethod
    def show_chat_info(chat_id, user_id, cq_id, msg_id):
        s = ChannelHandler._req(user_id)
        if not s: bot.answer_callback_query(cq_id,"اول گروه را انتخاب کنید",show_alert=True); return
        bot.answer_callback_query(cq_id,"در حال دریافت...")
        r = bot.get_chat(s)
        if r.get("ok"):
            i = r["result"]
            msg = f"اطلاعات\nشناسه: {i.get('id','')}\nنام: {i.get('title','')}\nنوع: {i.get('type','')}\nاعضا: {i.get('members_count','?')}"
        else: msg = f"خطا: {r.get('error')}"
        kb = bot.inline_keyboard([[{"text":"بازگشت","callback_data":"channel_main"}]])
        if msg_id: bot.edit_message_text(chat_id, msg_id, msg, reply_markup=kb)
        else: bot.send_message(chat_id, msg, reply_markup=kb)

    @staticmethod
    def show_members(chat_id, user_id, cq_id, msg_id):
        s = ChannelHandler._req(user_id)
        if not s: bot.answer_callback_query(cq_id,"اول گروه را انتخاب کنید",show_alert=True); return
        r = bot.get_chat_members_count(s)
        bot.send_message(chat_id, f"تعداد اعضا: {r.get('result','?')}" if r.get("ok") else f"خطا: {r.get('error')}")

    @staticmethod
    def show_admins(chat_id, user_id, cq_id, msg_id):
        s = ChannelHandler._req(user_id)
        if not s: bot.answer_callback_query(cq_id,"اول گروه را انتخاب کنید",show_alert=True); return
        r = bot.get_chat_administrators(s)
        if r.get("ok"):
            msg = f"مدیران ({len(r['result'])})\n\n"
            for a in r["result"]:
                u = a.get("user",{}); msg += f"- {u.get('first_name','')} ({u.get('id','')})\n"
            bot.send_message(chat_id, msg[:4000])
        else: bot.send_message(chat_id, f"خطا: {r.get('error')}")

    @staticmethod
    def make_invite_link(chat_id, user_id, cq_id, msg_id):
        s = ChannelHandler._req(user_id)
        if not s: bot.answer_callback_query(cq_id,"اول گروه را انتخاب کنید",show_alert=True); return
        r = bot.export_chat_invite_link(s)
        if not r.get("ok"): r = bot.create_chat_invite_link(s)
        bot.send_message(chat_id, f"لینک دعوت:\n{r.get('result') if isinstance(r.get('result'),str) else r.get('result',{}).get('invite_link','خطا')}" if r.get("ok") else f"خطا: {r.get('error')}")

    @staticmethod
    def _prompt(chat_id, user_id, cq_id, action, msg_text):
        s = ChannelHandler._req(user_id)
        if not s: bot.answer_callback_query(cq_id,"اول گروه را انتخاب کنید",show_alert=True); return
        bot.answer_callback_query(cq_id, msg_text)
        admin_selected_chat[action + str(user_id)] = s
        kb = bot.inline_keyboard([[{"text":"لغو","callback_data":"channel_main"}]])
        bot.send_message(chat_id, msg_text + ":", reply_markup=kb)

    @staticmethod
    def ban_user_prompt(chat_id, user_id, cq_id, msg_id): ChannelHandler._prompt(chat_id, user_id, cq_id, "ban_", "شناسه کاربر برای بن را وارد کنید")
    @staticmethod
    def unban_user_prompt(chat_id, user_id, cq_id, msg_id): ChannelHandler._prompt(chat_id, user_id, cq_id, "unban_", "شناسه کاربر برای آنبن را وارد کنید")
    @staticmethod
    def promote_user_prompt(chat_id, user_id, cq_id, msg_id): ChannelHandler._prompt(chat_id, user_id, cq_id, "promote_", "شناسه کاربر برای ارتقا را وارد کنید")
    @staticmethod
    def change_title_action(chat_id, user_id, cq_id, msg_id): ChannelHandler._prompt(chat_id, user_id, cq_id, "title_", "عنوان جدید را وارد کنید")
    @staticmethod
    def pin_message_prompt(chat_id, user_id, cq_id, msg_id): ChannelHandler._prompt(chat_id, user_id, cq_id, "pin_", "شناسه پیام را وارد کنید")
    @staticmethod
    def post_to_channel_prompt(chat_id, user_id, cq_id, msg_id): ChannelHandler._prompt(chat_id, user_id, cq_id, "post_", "متن پست را وارد کنید")
    @staticmethod
    def poll_action(chat_id, user_id, cq_id, msg_id): ChannelHandler._prompt(chat_id, user_id, cq_id, "poll_", "فرمت: سوال|گزینه1|گزینه2")

    @staticmethod
    def leave_chat_action(chat_id, user_id, cq_id, msg_id):
        s = ChannelHandler._req(user_id)
        if not s: bot.answer_callback_query(cq_id,"اول گروه را انتخاب کنید",show_alert=True); return
        r = bot.leave_chat(s)
        if r.get("ok"):
            bot.send_message(chat_id, "ربات خارج شد.")
            if str(user_id) in admin_selected_chat: del admin_selected_chat[str(user_id)]
        else: bot.send_message(chat_id, f"خطا: {r.get('error')}")
