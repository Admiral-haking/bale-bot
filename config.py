"""
تنظیمات اصلی ربات فروشگاه طب احمدی
"""
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

# ==================== تنظیمات ربات ====================
BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
API_BASE = os.getenv("BALE_API_BASE", "https://tapi.bale.ai")
API_URL = f"{API_BASE}/bot{BOT_TOKEN}"
FILE_API_URL = f"{API_BASE}/file/bot{BOT_TOKEN}"

# ==================== ادمین ارشد ====================
try:
    SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))
except (ValueError, TypeError):
    SUPER_ADMIN_ID = 0

# ==================== مسیر فایل‌ها ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
TICKETS_FILE = os.path.join(DATA_DIR, "tickets.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
CART_FILE = os.path.join(DATA_DIR, "cart.json")

# ==================== لاگینگ ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "bot.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("TabAhmadiBot")

# ==================== محدودیت‌ها ====================
MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
POLLING_TIMEOUT = 30
POLLING_LIMIT = 100
MAX_PRODUCTS_PER_PAGE = 5
MAX_CART_ITEMS = 20

# ==================== اطلاعات فروشگاه ====================
SHOP_NAME = "طب احمدی"
SHOP_DESCRIPTION = "فروشنده محصولات طبیعی ارگانیک"
SHOP_TAGLINE = "سبک زندگی سالم💚"
SHOP_PHONE = "@tebahmadi_admin"
SHOP_ADDRESS = "@tebahmadi13 (کانال آموزش و اخبار)"
SHOP_WEBSITE = "https://t.me/tebahmadi_admin"
SHOP_LOGO = "https://picsum.photos/200/200?random=shop"

# ==================== تنظیمات MongoDB ====================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "tebahmadi_bot")

# ==================== تنظیمات سفیر ====================
SAFIR_API_KEY = os.getenv("SAFIR_API_KEY", "")
SAFIR_BOT_ID = os.getenv("SAFIR_BOT_ID", "")
SAFIR_BASE_URL = "https://safir.bale.ai/api/v3"
SAFIR_MAX_FILE_SIZE = 500 * 1024 * 1024
