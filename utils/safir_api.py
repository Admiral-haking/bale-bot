"""
ماژول سفیر - سرویس ارسال پیام سازمانی بله
مستندات: https://safir.bale.ai/api/v3
"""
import json
import uuid
import logging
import requests
from typing import Optional, List
from config import SAFIR_API_KEY, SAFIR_BOT_ID, SAFIR_BASE_URL, SAFIR_MAX_FILE_SIZE, logger

logger = logging.getLogger("SafirAPI")


class SafirError(Exception):
    """خطای سفیر"""
    def __init__(self, code: int, description: str, phone: str = None):
        self.code = code
        self.description = description
        self.phone = phone
        super().__init__(f"[{code}] {description}" + (f" ({phone})" if phone else ""))


class SafirAPI:
    """
    سرویس ارسال پیام در بله (سفیر)
    - ارسال پیام متنی
    - ارسال پیام چندرسانه‌ای
    - ارسال پیام رمزدار (secure)
    - ارسال رمز یکبار مصرف (OTP)
    - بارگذاری فایل
    """

    ERROR_CODES = {
        2: "InternalServerError - خطای داخلی سرور",
        3: "RateLimitExceeded - بیش از حد مجاز پیام ارسال شده",
        4: "InvalidInput - ورودی JSON نامعتبر",
        8: "InvalidPhone - شماره اشتباه",
        17: "NotBaleUser - کاربر اکانت بله ندارد",
        20: "PaymentRequired - اعتبار کافی وجود ندارد",
        21: "MaximumContactLimitReached - محدودیت تعداد مخاطبین بازو",
    }

    def __init__(self, api_key: str = None, bot_id: int = None):
        self.api_key = api_key or SAFIR_API_KEY
        self.bot_id = bot_id or SAFIR_BOT_ID
        self.base_url = SAFIR_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "api-access-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        logger.info("🚀 SafirAPI initialized")

    def _validate_phone(self, phone: str) -> str:
        """اعتبارسنجی و نرمال‌سازی شماره تلفن"""
        # حذف کاراکترهای اضافی
        phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
        
        # اگر با 09 شروع شد، تبدیل کن
        if phone.startswith("09") and len(phone) == 11:
            phone = "98" + phone[1:]
        # اگر با 9 شروع شد، 98 بزن جلو
        elif phone.startswith("9") and len(phone) == 10:
            phone = "98" + phone
        # اگر با 0 شروع شد و طولش 11 هست
        elif phone.startswith("0") and len(phone) == 11:
            phone = "98" + phone[1:]
        
        if not phone.startswith("98") or len(phone) != 12:
            raise SafirError(8, "شماره تلفن نامعتبر است", phone)
        
        return phone

    def _request(self, endpoint: str, data: dict = None, files: dict = None) -> dict:
        """ارسال درخواست به API سفیر"""
        url = f"{self.base_url}/{endpoint}"
        try:
            if files:
                # برای آپلود فایل
                headers = {"api-access-key": self.api_key}
                resp = self.session.post(url, headers=headers, files=files, timeout=120)
            else:
                resp = self.session.post(url, json=data, timeout=30)

            resp.raise_for_status()
            result = resp.json()

            # بررسی خطا
            if result.get("error_data"):
                err = result["error_data"]
                if isinstance(err, list) and err:
                    err = err[0]
                code = err.get("code", 0)
                desc = err.get("description", "خطای ناشناخته")
                phone = err.get("phone_number", "")
                raise SafirError(code, desc, phone)

            return result

        except SafirError:
            raise
        except requests.exceptions.Timeout:
            raise SafirError(2, "مهلت درخواست تمام شد")
        except requests.exceptions.ConnectionError:
            raise SafirError(2, "خطا در اتصال به سرور")
        except requests.exceptions.HTTPError as e:
            raise SafirError(2, f"خطای HTTP: {e}")
        except json.JSONDecodeError:
            raise SafirError(4, "پاسخ نامعتبر JSON")
        except Exception as e:
            raise SafirError(2, f"خطای غیرمنتظره: {e}")

    # ==================== ارسال پیام ====================

    def send_message(
        self,
        phone: str,
        text: str = None,
        file_id: str = None,
        copy_text: str = None,
        is_secure: bool = False,
        otp: str = None,
        request_id: str = None
    ) -> dict:
        """
        ارسال پیام از طریق سرویس سفیر
        
        Args:
            phone: شماره تلفن مقصد (با 98 شروع شود)
            text: متن پیام
            file_id: شناسه فایل آپلود شده
            copy_text: متن قابل کپی
            is_secure: پیام رمزدار
            otp: رمز یکبار مصرف
            request_id: شناسه درخواست (برای جلوگیری از ارسال تکراری)
        
        Returns:
            dict: {"message_id": "...", "error_data": null}
        """
        phone = self._validate_phone(phone)
        
        # ساختار پایه
        body = {
            "bot_id": self.bot_id,
            "phone_number": phone,
            "message_data": {}
        }

        if request_id:
            body["request_id"] = request_id
        else:
            body["request_id"] = str(uuid.uuid4())

        # تعیین نوع پیام
        if otp:
            # پیام رمز یکبار مصرف
            body["message_data"]["otp_message"] = {"otp": otp}
        else:
            # پیام عادی (متن/چندرسانه‌ای)
            message = {}
            if text:
                message["text"] = text
            if file_id:
                message["file_id"] = file_id
            if copy_text:
                message["copy_text"] = copy_text
            
            body["message_data"]["message"] = message
            if is_secure:
                body["message_data"]["is_secure"] = True

        result = self._request("send_message", data=body)
        logger.info(f"✅ پیام ارسال شد به {phone} - message_id: {result.get('message_id')}")
        return result

    def send_text(
        self,
        phone: str,
        text: str,
        copy_text: str = None,
        is_secure: bool = False
    ) -> dict:
        """ارسال پیام متنی ساده"""
        return self.send_message(phone=phone, text=text, copy_text=copy_text, is_secure=is_secure)

    def send_media(
        self,
        phone: str,
        file_id: str,
        caption: str = None,
        is_secure: bool = False
    ) -> dict:
        """ارسال پیام چندرسانه‌ای (عکس، ویدیو، فایل)"""
        return self.send_message(phone=phone, text=caption, file_id=file_id, is_secure=is_secure)

    def send_secure(
        self,
        phone: str,
        text: str,
        file_id: str = None
    ) -> dict:
        """ارسال پیام رمزدار (نیازمند رمز عبور برای مشاهده)"""
        return self.send_message(phone=phone, text=text, file_id=file_id, is_secure=True)

    def send_otp(
        self,
        phone: str,
        otp_code: str
    ) -> dict:
        """ارسال رمز یکبار مصرف (OTP) - پیام رسمی با برند"""
        if not otp_code.isdigit():
            raise SafirError(4, "رمز یکبار مصرف باید عددی باشد")
        return self.send_message(phone=phone, otp=otp_code)

    def send_bulk(
        self,
        phones: List[str],
        text: str = None,
        file_id: str = None,
        otp: str = None,
        is_secure: bool = False
    ) -> List[dict]:
        """
        ارسال پیام به چند شماره
        
        Returns:
            list of results
        """
        results = []
        for phone in phones:
            try:
                result = self.send_message(
                    phone=phone,
                    text=text,
                    file_id=file_id,
                    is_secure=is_secure,
                    otp=otp
                )
                results.append({"phone": phone, "success": True, "data": result})
            except SafirError as e:
                results.append({"phone": phone, "success": False, "error": str(e)})
            except Exception as e:
                results.append({"phone": phone, "success": False, "error": str(e)})
        return results

    # ==================== بارگذاری فایل ====================

    def upload_file(self, file_path: str) -> str:
        """
        آپلود فایل در سرور بله و دریافت شناسه یکتای فایل
        
        Args:
            file_path: مسیر فایل
        
        Returns:
            str: file_id شناسه یکتای فایل
        """
        import os
        if not os.path.exists(file_path):
            raise SafirError(4, f"فایل {file_path} یافت نشد")

        file_size = os.path.getsize(file_path)
        if file_size > SAFIR_MAX_FILE_SIZE:
            raise SafirError(4, f"حجم فایل بیشتر از حد مجاز (500MB)")

        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
            result = self._request("upload_file", files=files)

        file_id = result.get("file_id")
        if file_id:
            logger.info(f"✅ فایل آپلود شد: {file_id}")
            return file_id
        else:
            raise SafirError(2, "خطا در دریافت شناسه فایل")

    # ==================== متدهای کمکی ====================

    def validate_config(self) -> bool:
        """بررسی اعتبار تنظیمات سفیر"""
        if not self.api_key or self.api_key == "your_safir_api_key_here":
            logger.warning("⚠️ SAFIR_API_KEY تنظیم نشده")
            return False
        if not self.bot_id or self.bot_id == "your_bot_id_here":
            logger.warning("⚠️ SAFIR_BOT_ID تنظیم نشده")
            return False
        try:
            self.bot_id = int(self.bot_id)
        except (ValueError, TypeError):
            logger.warning("⚠️ SAFIR_BOT_ID معتبر نیست")
            return False
        return True

    @staticmethod
    def get_error_message(code: int) -> str:
        """دریافت توضیح خطا بر اساس کد"""
        return SafirAPI.ERROR_CODES.get(code, f"خطای ناشناخته (کد {code})")


# نمونه سراسری
safir = SafirAPI()
