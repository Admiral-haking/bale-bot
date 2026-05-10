"""
کتابخانه ارتباط با API بازوی بله
مستندات: https://tapi.bale.ai
"""
import json
import logging
import os
from typing import Optional
import requests
from config import API_URL, FILE_API_URL, logger

logger = logging.getLogger("BaleAPI")


class BaleAPI:
    """کلاس اصلی ارتباط با API بله"""

    def __init__(self, token: str = None):
        self.token = token
        self.api_url = API_URL
        self.file_api_url = FILE_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        files: dict = None,
        data: dict = None
    ) -> dict:
        """ارسال درخواست به API بله"""
        url = f"{self.api_url}/{endpoint}"

        # نسخه امن لاگ (بدون توکن)
        safe_url = f"{url[:url.rfind('/')+1]}{endpoint}"

        try:
            if files:
                resp = self.session.post(url, params=params, files=files, data=data, timeout=60)
            else:
                if data:
                    resp = self.session.post(url, params=params, json=data, timeout=30)
                else:
                    resp = self.session.get(url, params=params, timeout=30)

            resp.raise_for_status()
            result = resp.json()

            if not result.get("ok"):
                error_desc = result.get('description', 'Unknown error')
                error_code = result.get('error_code', 'N/A')
                logger.error(f"API Error [{endpoint}]: {error_desc} (code: {error_code})")
                return {"ok": False, "error": error_desc}

            return {"ok": True, "result": result.get("result")}

        except requests.exceptions.Timeout:
            logger.error(f"Timeout in [{endpoint}]")
            return {"ok": False, "error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error in [{endpoint}]")
            return {"ok": False, "error": "Connection error"}
        except requests.exceptions.HTTPError as e:
            # 400 روی answerCallbackQuery یعنی قبلاً پاسخ داده شده - بی‌خطر
            if "400" in str(e) and "answerCallbackQuery" in endpoint:
                return {"ok": False, "error": "already_answered"}
            logger.error(f"HTTP error in [{endpoint}]: {e}")
            return {"ok": False, "error": str(e)}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response in [{endpoint}]")
            return {"ok": False, "error": "Invalid JSON response"}
        except Exception as e:
            logger.error(f"Unexpected error in [{endpoint}]: {e}")
            return {"ok": False, "error": str(e)}

    # ==================== متدهای پایه ====================

    def get_me(self) -> dict:
        """دریافت اطلاعات بازو (تست توکن)"""
        return self._request("GET", "getMe")

    def get_updates(self, offset: int = 0, limit: int = 100, timeout: int = 30) -> dict:
        """دریافت آپدیت‌ها با long polling"""
        params = {"offset": offset, "limit": limit, "timeout": timeout}
        return self._request("GET", "getUpdates", params=params)

    # ==================== ارسال پیام ====================

    def send_message(
        self,
        chat_id: str,
        text: str,
        reply_to_message_id: int = None,
        reply_markup: dict = None
    ) -> dict:
        """ارسال پیام متنی"""
        if not text:
            return {"ok": False, "error": "Empty text"}
        data = {"chat_id": chat_id, "text": text[:4096]}
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "sendMessage", data=data)

    def send_photo(
        self,
        chat_id: str,
        photo: str,
        caption: str = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None
    ) -> dict:
        """ارسال تصویر"""
        data = {"chat_id": chat_id, "photo": photo}
        if caption:
            data["caption"] = caption[:1024]
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "sendPhoto", data=data)

    def send_document(
        self,
        chat_id: str,
        document: str,
        caption: str = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None
    ) -> dict:
        """ارسال فایل"""
        data = {"chat_id": chat_id, "document": document}
        if caption:
            data["caption"] = caption[:1024]
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "sendDocument", data=data)

    def send_audio(
        self,
        chat_id: str,
        audio: str,
        caption: str = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None
    ) -> dict:
        """ارسال فایل صوتی (موسیقی)"""
        data = {"chat_id": chat_id, "audio": audio}
        if caption:
            data["caption"] = caption[:1024]
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "sendAudio", data=data)

    def send_video(
        self,
        chat_id: str,
        video: str,
        caption: str = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None
    ) -> dict:
        """ارسال ویدیو"""
        data = {"chat_id": chat_id, "video": video}
        if caption:
            data["caption"] = caption[:1024]
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "sendVideo", data=data)

    def send_animation(
        self,
        chat_id: str,
        animation: str,
        reply_to_message_id: int = None,
        reply_markup: dict = None
    ) -> dict:
        """ارسال انیمیشن (GIF)"""
        data = {"chat_id": chat_id, "animation": animation}
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "sendAnimation", data=data)

    def send_voice(
        self,
        chat_id: str,
        voice: str,
        caption: str = None,
        reply_to_message_id: int = None
    ) -> dict:
        """ارسال پیام صوتی"""
        data = {"chat_id": chat_id, "voice": voice}
        if caption:
            data["caption"] = caption[:1024]
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        return self._request("POST", "sendVoice", data=data)

    def send_media_group(
        self,
        chat_id: str,
        media: list,
        reply_to_message_id: int = None
    ) -> dict:
        """ارسال آلبوم (گروهی از رسانه‌ها)"""
        data = {"chat_id": chat_id, "media": json.dumps(media)}
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        return self._request("POST", "sendMediaGroup", data=data)

    def send_location(
        self,
        chat_id: str,
        latitude: float,
        longitude: float,
        horizontal_accuracy: float = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None
    ) -> dict:
        """ارسال موقعیت مکانی"""
        data = {"chat_id": chat_id, "latitude": latitude, "longitude": longitude}
        if horizontal_accuracy:
            data["horizontal_accuracy"] = horizontal_accuracy
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "sendLocation", data=data)

    def send_contact(
        self,
        chat_id: str,
        phone_number: str,
        first_name: str,
        last_name: str = None,
        reply_to_message_id: int = None,
        reply_markup: dict = None
    ) -> dict:
        """ارسال مخاطب"""
        data = {"chat_id": chat_id, "phone_number": phone_number, "first_name": first_name}
        if last_name:
            data["last_name"] = last_name
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "sendContact", data=data)

    def send_chat_action(self, chat_id: str, action: str) -> dict:
        """نمایش وضعیت در حال انجام"""
        data = {"chat_id": chat_id, "action": action}
        return self._request("POST", "sendChatAction", data=data)

    def forward_message(
        self,
        chat_id: str,
        from_chat_id: str,
        message_id: int
    ) -> dict:
        """باز ارسال پیام"""
        data = {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id
        }
        return self._request("POST", "forwardMessage", data=data)

    def copy_message(
        self,
        chat_id: str,
        from_chat_id: str,
        message_id: int
    ) -> dict:
        """کپی پیام (بدون لینک به پیام اصلی)"""
        data = {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id
        }
        return self._request("POST", "copyMessage", data=data)

    # ==================== فایل ====================

    def get_file(self, file_id: str) -> dict:
        """دریافت اطلاعات فایل برای دانلود"""
        data = {"file_id": file_id}
        return self._request("POST", "getFile", data=data)

    def download_file(self, file_path: str, save_path: str) -> bool:
        """دانلود فایل از سرور بله"""
        url = f"{self.file_api_url}/{file_path}"
        try:
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"File downloaded: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    # ==================== صفحه‌کلید ====================

    @staticmethod
    def inline_keyboard(buttons: list) -> dict:
        """ساخت صفحه‌کلید inline"""
        return {"inline_keyboard": buttons}

    @staticmethod
    def reply_keyboard(buttons: list, resize: bool = True, one_time: bool = False) -> dict:
        """ساخت صفحه‌کلید معمولی"""
        return {
            "keyboard": buttons,
            "resize_keyboard": resize,
            "one_time_keyboard": one_time
        }

    @staticmethod
    def reply_keyboard_remove() -> dict:
        """حذف صفحه‌کلید"""
        return {"remove_keyboard": True}

    # ==================== ویرایش/حذف پیام ====================

    def edit_message_text(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        reply_markup: dict = None
    ) -> dict:
        """ویرایش متن پیام"""
        data = {"chat_id": chat_id, "message_id": message_id, "text": text[:4096]}
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "editMessageText", data=data)

    def edit_message_caption(
        self,
        chat_id: str,
        message_id: int,
        caption: str = None,
        reply_markup: dict = None
    ) -> dict:
        """ویرایش زیرنویس پیام"""
        data = {"chat_id": chat_id, "message_id": message_id}
        if caption:
            data["caption"] = caption[:1024]
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "editMessageCaption", data=data)

    def edit_message_reply_markup(
        self,
        chat_id: str,
        message_id: int,
        reply_markup: dict = None
    ) -> dict:
        """ویرایش صفحه‌کلید پیام"""
        data = {"chat_id": chat_id, "message_id": message_id}
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "editMessageReplyMarkup", data=data)

    def delete_message(self, chat_id: str, message_id: int) -> dict:
        """حذف پیام"""
        data = {"chat_id": chat_id, "message_id": message_id}
        return self._request("POST", "deleteMessage", data=data)

    # ==================== Callback Query ====================

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: str = None,
        show_alert: bool = False
    ) -> dict:
        """پاسخ به callback query"""
        if not callback_query_id or str(callback_query_id) in ("None", "0", ""):
            return {"ok": False, "error": "invalid_cq_id"}
        data = {"callback_query_id": callback_query_id}
        if text:
            data["text"] = text[:200]
        if show_alert:
            data["show_alert"] = True
        return self._request("POST", "answerCallbackQuery", data=data)

    # ==================== مدیریت گروه ====================

    def ban_chat_member(self, chat_id: str, user_id: int) -> dict:
        """مسدود کردن کاربر"""
        data = {"chat_id": chat_id, "user_id": user_id}
        return self._request("POST", "banChatMember", data=data)

    def unban_chat_member(self, chat_id: str, user_id: int, only_if_banned: bool = False) -> dict:
        """رفع مسدودیت کاربر"""
        data = {"chat_id": chat_id, "user_id": user_id}
        if only_if_banned:
            data["only_if_banned"] = True
        return self._request("POST", "unbanChatMember", data=data)

    def promote_chat_member(
        self, chat_id: str, user_id: int,
        can_change_info: bool = False,
        can_post_messages: bool = False,
        can_edit_messages: bool = False,
        can_delete_messages: bool = False,
        can_manage_video_chats: bool = False,
        can_invite_users: bool = False,
        can_restrict_members: bool = False,
        can_pin_messages: bool = False,
        can_promote_members: bool = False
    ) -> dict:
        """ارتقا کاربر به مدیر"""
        data = {
            "chat_id": chat_id, "user_id": user_id,
            "can_change_info": can_change_info,
            "can_post_messages": can_post_messages,
            "can_edit_messages": can_edit_messages,
            "can_delete_messages": can_delete_messages,
            "can_manage_video_chats": can_manage_video_chats,
            "can_invite_users": can_invite_users,
            "can_restrict_members": can_restrict_members,
            "can_pin_messages": can_pin_messages,
            "can_promote_members": can_promote_members
        }
        return self._request("POST", "promoteChatMember", data=data)

    def leave_chat(self, chat_id: str) -> dict:
        """خروج بازو از گروه"""
        data = {"chat_id": chat_id}
        return self._request("POST", "leaveChat", data=data)

    def get_chat(self, chat_id: str) -> dict:
        """دریافت اطلاعات گفتگو"""
        data = {"chat_id": chat_id}
        return self._request("POST", "getChat", data=data)

    def get_chat_administrators(self, chat_id: str) -> dict:
        """لیست مدیران"""
        data = {"chat_id": chat_id}
        return self._request("POST", "getChatAdministrators", data=data)

    def get_chat_members_count(self, chat_id: str) -> dict:
        """تعداد اعضا"""
        data = {"chat_id": chat_id}
        return self._request("POST", "getChatMembersCount", data=data)

    def get_chat_member(self, chat_id: str, user_id: int) -> dict:
        """اطلاعات یک عضو"""
        data = {"chat_id": chat_id, "user_id": user_id}
        return self._request("POST", "getChatMember", data=data)

    def unpin_all_chat_messages(self, chat_id: str) -> dict:
        """حذف همه پین‌ها"""
        data = {"chat_id": chat_id}
        return self._request("POST", "unpinAllChatMessages", data=data)

    def set_chat_title(self, chat_id: str, title: str) -> dict:
        """تغییر عنوان گروه"""
        data = {"chat_id": chat_id, "title": title}
        return self._request("POST", "setChatTitle", data=data)

    def set_chat_description(self, chat_id: str, description: str) -> dict:
        """تغییر توضیحات گروه"""
        data = {"chat_id": chat_id, "description": description}
        return self._request("POST", "setChatDescription", data=data)

    def delete_chat_photo(self, chat_id: str) -> dict:
        """حذف عکس گروه"""
        data = {"chat_id": chat_id}
        return self._request("POST", "deleteChatPhoto", data=data)

    def export_chat_invite_link(self, chat_id: str) -> dict:
        """لینک دعوت جدید"""
        data = {"chat_id": chat_id}
        return self._request("POST", "exportChatInviteLink", data=data)

    def create_chat_invite_link(self, chat_id: str) -> dict:
        """ساخت لینک دعوت"""
        data = {"chat_id": chat_id}
        return self._request("POST", "createChatInviteLink", data=data)

    def revoke_chat_invite_link(self, chat_id: str, invite_link: str) -> dict:
        """ابطال لینک دعوت"""
        data = {"chat_id": chat_id, "invite_link": invite_link}
        return self._request("POST", "revokeChatInviteLink", data=data)

    # ==================== وب‌هوک ====================

    def set_webhook(self, url: str) -> dict:
        """تنظیم وب‌هوک"""
        data = {"url": url}
        return self._request("POST", "setWebhook", data=data)

    def delete_webhook(self) -> dict:
        """حذف وب‌هوک"""
        return self._request("POST", "deleteWebhook")

    def get_webhook_info(self) -> dict:
        """اطلاعات وب‌هوک فعلی"""
        return self._request("GET", "getWebhookInfo")

    # ==================== پرداخت ====================

    def send_invoice(
        self,
        chat_id: str,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        prices: list,
        photo_url: str = None,
        reply_to_message_id: int = None
    ) -> dict:
        """ارسال درخواست پول"""
        data = {
            "chat_id": chat_id,
            "title": title[:32],
            "description": description[:255],
            "payload": payload,
            "provider_token": provider_token,
            "prices": json.dumps(prices),
        }
        if photo_url:
            data["photo_url"] = photo_url
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        return self._request("POST", "sendInvoice", data=data)

    def create_invoice_link(
        self,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        prices: list
    ) -> dict:
        """ساخت لینک پرداخت برای مینی‌اپ"""
        data = {
            "title": title[:32],
            "description": description[:255],
            "payload": payload,
            "provider_token": provider_token,
            "prices": json.dumps(prices),
        }
        return self._request("POST", "createInvoiceLink", data=data)

    def answer_pre_checkout_query(
        self,
        pre_checkout_query_id: str,
        ok: bool,
        error_message: str = None
    ) -> dict:
        """تأیید/رد پرداخت قبل از نهایی شدن"""
        data = {
            "pre_checkout_query_id": pre_checkout_query_id,
            "ok": ok
        }
        if not ok and error_message:
            data["error_message"] = error_message
        return self._request("POST", "answerPreCheckoutQuery", data=data)

    def inquire_transaction(self, transaction_id: str) -> dict:
        """استعلام تراکنش"""
        data = {"transaction_id": transaction_id}
        return self._request("POST", "inquireTransaction", data=data)

    # ==================== استیکر ====================

    def upload_sticker_file(self, user_id: int, sticker_path: str) -> dict:
        """آپلود فایل استیکر"""
        with open(sticker_path, "rb") as f:
            files = {"sticker": f}
            data = {"user_id": user_id}
            return self._request("POST", "uploadStickerFile", data=data, files=files)

    # ==================== نظرسنجی ====================

    def ask_review(self, user_id: int, delay_seconds: int = 10) -> dict:
        """درخواست ثبت نظر از کاربر"""
        data = {"user_id": user_id, "delay_seconds": delay_seconds}
        return self._request("POST", "askReview", data=data)

    # ==================== مدیریت گروه و کانال - پیشرفته ====================

    def restrict_chat_member(
        self,
        chat_id: str,
        user_id: int,
        permissions: dict = None,
        until_date: int = None
    ) -> dict:
        """محدود کردن کاربر در گروه"""
        data = {"chat_id": chat_id, "user_id": user_id}
        if permissions:
            data["permissions"] = permissions
        if until_date:
            data["until_date"] = until_date
        return self._request("POST", "restrictChatMember", data=data)

    def send_poll(
        self,
        chat_id: str,
        question: str,
        options: list,
        is_anonymous: bool = True,
        allows_multiple_answers: bool = False,
        correct_option_id: int = None,
        explanation: str = None,
        open_period: int = None,
        close_date: int = None,
        is_closed: bool = False,
        reply_markup: dict = None
    ) -> dict:
        """ارسال نظرسنجی به گروه یا کانال"""
        data = {
            "chat_id": chat_id,
            "question": question[:300],
            "options": [{"text": opt[:100]} for opt in options],
            "is_anonymous": is_anonymous,
            "allows_multiple_answers": allows_multiple_answers,
            "is_closed": is_closed
        }
        if correct_option_id is not None:
            data["type"] = "quiz"
            data["correct_option_id"] = correct_option_id
        if explanation:
            data["explanation"] = explanation[:200]
        if open_period:
            data["open_period"] = open_period
        if close_date:
            data["close_date"] = close_date
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "sendPoll", data=data)

    def stop_poll(self, chat_id: str, message_id: int, reply_markup: dict = None) -> dict:
        """متوقف کردن نظرسنجی"""
        data = {"chat_id": chat_id, "message_id": message_id}
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("POST", "stopPoll", data=data)

    def set_chat_permissions(self, chat_id: str, permissions: dict) -> dict:
        """تنظیم دسترسی‌های پیش‌فرض گروه"""
        data = {"chat_id": chat_id, "permissions": permissions}
        return self._request("POST", "setChatPermissions", data=data)

    def set_chat_administrator_custom_title(
        self, chat_id: str, user_id: int, custom_title: str
    ) -> dict:
        """تنظیم عنوان سفارشی برای ادمین"""
        data = {"chat_id": chat_id, "user_id": user_id, "custom_title": custom_title[:16]}
        return self._request("POST", "setChatAdministratorCustomTitle", data=data)

    def set_chat_sticker_set(self, chat_id: str, sticker_set_name: str) -> dict:
        """تنظیم مجموعه استیکر گروه"""
        data = {"chat_id": chat_id, "sticker_set_name": sticker_set_name}
        return self._request("POST", "setChatStickerSet", data=data)

    def delete_chat_sticker_set(self, chat_id: str) -> dict:
        """حذف مجموعه استیکر گروه"""
        data = {"chat_id": chat_id}
        return self._request("POST", "deleteChatStickerSet", data=data)

    def approve_chat_join_request(self, chat_id: str, user_id: int) -> dict:
        """تأیید درخواست عضویت در گروه"""
        data = {"chat_id": chat_id, "user_id": user_id}
        return self._request("POST", "approveChatJoinRequest", data=data)

    def decline_chat_join_request(self, chat_id: str, user_id: int) -> dict:
        """رد درخواست عضویت در گروه"""
        data = {"chat_id": chat_id, "user_id": user_id}
        return self._request("POST", "declineChatJoinRequest", data=data)

    # ==================== مدیریت پیام در گروه و کانال ====================

    def send_message_to_channel(
        self,
        chat_id: str,
        text: str,
        disable_notification: bool = False,
        reply_markup: dict = None
    ) -> dict:
        """ارسال پیام به کانال (بدون نیاز به reply_to)"""
        return self.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )

    def pin_chat_message(self, chat_id: str, message_id: int, disable_notification: bool = False) -> dict:
        """پین کردن پیام در گروه/کانال"""
        data = {"chat_id": chat_id, "message_id": message_id, "disable_notification": disable_notification}
        return self._request("POST", "pinChatMessage", data=data)

    def unpin_chat_message(self, chat_id: str, message_id: int = None) -> dict:
        """حذف پین پیام"""
        data = {"chat_id": chat_id}
        if message_id:
            data["message_id"] = message_id
        return self._request("POST", "unpinChatMessage", data=data)


# نمونه global از API
bot = BaleAPI()
