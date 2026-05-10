"""
مدیریت سفارش - با کد رهگیری و اطلاع رسانی
"""
import logging
from utils.bale_api import bot
from utils.database import Database
from config import SHOP_NAME, logger

logger = logging.getLogger("OrderHandler")


class OrderHandler:
    user_states = {}

    @staticmethod
    def start_order(chat_id, user_id, product_id):
        products = Database.get_products()
        product = next((p for p in products if str(p.get('id','')) == product_id), None)
        if not product: bot.send_message(chat_id, "محصول یافت نشد."); return False
        OrderHandler.user_states[str(chat_id)] = {
            'state': 'waiting_name',
            'data': {'user_id': user_id, 'from_cart': False,
                     'items': [{'product_id': product_id, 'name': product.get('name',''), 'price': product.get('price',''), 'quantity': 1}],
                     'total_price': product.get('price','')}
        }
        kb = bot.inline_keyboard([[{"text": "لغو سفارش", "callback_data": "order_cancel"}]])
        bot.send_message(chat_id, f"ثبت سفارش\nمحصول: {product.get('name','')}\nقیمت: {product.get('price','')}\n\nمرحله ۱ از ۳: نام و نام خانوادگی خود را وارد کنید:", reply_markup=kb)
        return True

    @staticmethod
    def start_order_from_cart(chat_id, user_id):
        cart = Database.get_cart(user_id)
        if not cart: bot.send_message(chat_id, "سبد خرید خالی است."); return False
        items_summary = "\n".join([f"- {i.get('name','')} x{i.get('quantity',1)}" for i in cart])
        OrderHandler.user_states[str(chat_id)] = {
            'state': 'waiting_name',
            'data': {'user_id': user_id, 'from_cart': True, 'items': cart, 'total_price': f"{sum(i.get('quantity',1) for i in cart)} قلم"}
        }
        Database.clear_cart(user_id)
        kb = bot.inline_keyboard([[{"text": "لغو سفارش", "callback_data": "order_cancel"}]])
        bot.send_message(chat_id, f"ثبت سفارش از سبد خرید\n\n{items_summary}\n\nمرحله ۱ از ۳: نام و نام خانوادگی خود را وارد کنید:", reply_markup=kb)
        return True

    @staticmethod
    def handle_message(chat_id, user_id, text):
        state = OrderHandler.user_states.get(str(chat_id))
        if not state: return False
        current = state['state']
        data = state['data']
        kb = bot.inline_keyboard([[{"text": "لغو سفارش", "callback_data": "order_cancel"}]])

        if current == 'waiting_name':
            if not text or len(text.strip()) < 3:
                bot.send_message(chat_id, "نام حداقل ۳ حرف.", reply_markup=kb); return True
            data['customer_name'] = text.strip()
            state['state'] = 'waiting_phone'
            bot.send_message(chat_id, f"نام ثبت شد.\nمرحله ۲ از ۳: شماره موبایل (مثال: 09121234567):", reply_markup=kb); return True
        elif current == 'waiting_phone':
            phone = text.strip().replace(" ","").replace("-","").replace("+","")
            if not (phone.startswith("09") and len(phone)==11) and not (phone.startswith("98") and len(phone)==12):
                bot.send_message(chat_id, "شماره معتبر نیست.\nمثال: 09121234567", reply_markup=kb); return True
            data['customer_phone'] = phone
            state['state'] = 'waiting_address'
            bot.send_message(chat_id, f"شماره ثبت شد.\nمرحله ۳ از ۳: آدرس خود را وارد کنید:", reply_markup=kb); return True
        elif current == 'waiting_address':
            if not text or len(text.strip()) < 10:
                bot.send_message(chat_id, "آدرس حداقل ۱۰ حرف.", reply_markup=kb); return True
            data['customer_address'] = text.strip()
            state['state'] = 'waiting_confirm'
            items = "\n".join([f"- {i.get('name','')} x{i.get('quantity',1)}" for i in data['items']])
            msg = f"خلاصه سفارش\n\n{items}\n\nنام: {data['customer_name']}\nموبایل: {data['customer_phone']}\nآدرس: {data['customer_address']}\n\nاطلاعات صحیح است؟"
            kb = bot.inline_keyboard([
                [{"text": "تایید و ثبت", "callback_data": "order_confirm"}],
                [{"text": "لغو", "callback_data": "order_cancel"}]
            ])
            bot.send_message(chat_id, msg, reply_markup=kb); return True
        return False

    @staticmethod
    def confirm_order(chat_id, user_id):
        state = OrderHandler.user_states.get(str(chat_id))
        if not state or state['state'] != 'waiting_confirm':
            bot.send_message(chat_id, "خطا: سفارشی در انتظار نیست."); return
        data = state['data']
        
        # ثبت سفارش با کد رهگیری
        order_id, tracking_code = Database.create_order(
            customer_id=user_id, items=data['items'],
            total_price=data.get('total_price',''),
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            customer_address=data['customer_address']
        )
        
        if str(chat_id) in OrderHandler.user_states:
            del OrderHandler.user_states[str(chat_id)]
        
        # پیام تایید به کاربر با کد رهگیری
        msg = (
            f"سفارش شما ثبت شد.\n\n"
            f"کد سفارش: {order_id}\n"
            f"کد رهگیری: {tracking_code}\n\n"
            f"این کد را برای پیگیری سفارش خود نگه دارید.\n"
            f"با شما تماس گرفته خواهد شد."
        )
        bot.send_message(chat_id, msg)
        
        # اطلاع به ادمین‌ها
        admins = Database.get_all_admin_ids()
        items = "\n".join([f"- {i.get('name','')} x{i.get('quantity',1)}" for i in data['items']])
        admin_msg = (
            f"سفارش جدید\n"
            f"کد: {order_id}\n"
            f"رهگیری: {tracking_code}\n"
            f"مشتری: {data['customer_name']} ({user_id})\n"
            f"تلفن: {data['customer_phone']}\n"
            f"آدرس: {data['customer_address']}\n"
            f"اقلام:\n{items}"
        )
        kb = bot.inline_keyboard([
            [{"text": "تایید سفارش", "callback_data": f"change_status_{order_id}_confirmed"}],
            [{"text": "مدیریت سفارشات", "callback_data": "admin_orders"}]
        ])
        for admin_id in admins:
            if str(admin_id) != str(user_id):
                try: bot.send_message(str(admin_id), admin_msg, reply_markup=kb)
                except: pass
        logger.info(f"سفارش جدید: {order_id} - رهگیری: {tracking_code} - {data['customer_name']}")

    @staticmethod
    def cancel_order(chat_id, user_id):
        if str(chat_id) in OrderHandler.user_states:
            state = OrderHandler.user_states[str(chat_id)]
            if state['data'].get('from_cart'):
                for item in state['data'].get('items',[]):
                    Database.add_to_cart(user_id, item.get('product_id',''), item.get('quantity',1))
            del OrderHandler.user_states[str(chat_id)]
        bot.send_message(chat_id, "سفارش لغو شد.\nهر وقت خواستید دوباره سفارش دهید.")
