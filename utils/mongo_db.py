"""
سیستم دیتابیس MongoDB برای ربات فروشگاه طب احمدی
تمامی عملیات اتمیک و با قابلیت اطمینان بالا
"""
import os
from datetime import datetime, timedelta
from pymongo import MongoClient, errors
from config import MONGO_URI, MONGO_DB_NAME, SUPER_ADMIN_ID, logger

class MongoDatabase:
    """مدیریت دیتابیس MongoDB"""

    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[MONGO_DB_NAME]
            self.client.server_info()
            self.connected = True
            self._ensure_indexes()
            logger.info("✅ MongoDB connected successfully")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.connected = False

    def _ensure_indexes(self):
        """ایندکس‌های مورد نیاز"""
        self.db.users.create_index("chat_id", unique=True)
        self.db.orders.create_index("order_id", unique=True)
        self.db.orders.create_index("tracking_code", unique=True)
        self.db.tickets.create_index("ticket_id", unique=True)
        self.db.products.create_index("id", unique=True)
        self.db.admins.create_index("user_id", unique=True)
        self.db.carts.create_index("user_id", unique=True)
        self.db.counters.create_index("name", unique=True)

    def _get_counter(self, name):
        """دریافت و افزایش شمارنده اتمیک"""
        result = self.db.counters.find_one_and_update(
            {"name": name},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=True
        )
        return result["value"]

    # ==================== ادمین‌ها ====================

    def get_admins_list(self):
        docs = self.db.admins.find({}, {"user_id": 1, "_id": 0})
        return [d["user_id"] for d in docs]

    def is_admin(self, user_id):
        try:
            uid = int(user_id) if not isinstance(user_id, int) else user_id
            return uid == SUPER_ADMIN_ID or bool(self.db.admins.find_one({"user_id": uid}))
        except: return False

    def is_super_admin(self, user_id):
        try:
            uid = int(user_id) if not isinstance(user_id, int) else user_id
            return uid == SUPER_ADMIN_ID and SUPER_ADMIN_ID != 0
        except: return False

    def add_admin(self, user_id):
        try:
            uid = int(user_id) if not isinstance(user_id, int) else user_id
            if uid == SUPER_ADMIN_ID: return False
            self.db.admins.update_one(
                {"user_id": uid},
                {"$setOnInsert": {"user_id": uid, "created_at": datetime.now()}},
                upsert=True
            )
            return True
        except: return False

    def remove_admin(self, user_id):
        try:
            uid = int(user_id) if not isinstance(user_id, int) else user_id
            result = self.db.admins.delete_one({"user_id": uid})
            return result.deleted_count > 0
        except: return False

    def get_all_admin_ids(self):
        admins = self.get_admins_list()
        if SUPER_ADMIN_ID and SUPER_ADMIN_ID not in admins:
            admins.insert(0, SUPER_ADMIN_ID)
        return admins

    # ==================== کاربران ====================

    def register_user(self, chat_id, user_info: dict):
        now = datetime.now()
        result = self.db.users.update_one(
            {"chat_id": str(chat_id)},
            {
                "$setOnInsert": {
                    "chat_id": str(chat_id),
                    "first_name": user_info.get("first_name", ""),
                    "last_name": user_info.get("last_name", ""),
                    "username": user_info.get("username", ""),
                    "phone": user_info.get("phone", ""),
                    "first_seen": now,
                    "is_blocked": False,
                    "notes": ""
                },
                "$set": {"last_seen": now},
                "$inc": {"messages_count": 1}
            },
            upsert=True
        )
        # Update name/username if provided
        updates = {}
        if user_info.get("first_name"): updates["first_name"] = user_info["first_name"]
        if user_info.get("last_name"): updates["last_name"] = user_info["last_name"]
        if user_info.get("username"): updates["username"] = user_info["username"]
        if updates:
            self.db.users.update_one({"chat_id": str(chat_id)}, {"$set": updates})
        return True

    def get_all_users(self):
        docs = self.db.users.find().sort("last_seen", -1)
        return {d["chat_id"]: d for d in docs}

    def get_all_chat_ids(self):
        docs = self.db.users.find({"is_blocked": {"$ne": True}}, {"chat_id": 1})
        return [d["chat_id"] for d in docs]

    def get_user_count(self):
        return self.db.users.count_documents({})

    def get_user_info(self, chat_id):
        doc = self.db.users.find_one({"chat_id": str(chat_id)})
        return doc or {}

    def block_user(self, chat_id):
        result = self.db.users.update_one({"chat_id": str(chat_id)}, {"$set": {"is_blocked": True}})
        return result.modified_count > 0

    def unblock_user(self, chat_id):
        result = self.db.users.update_one({"chat_id": str(chat_id)}, {"$set": {"is_blocked": False}})
        return result.modified_count > 0

    def get_user_orders_count(self, chat_id):
        return self.db.orders.count_documents({"customer_id": str(chat_id)})

    # ==================== تیکت‌ها ====================

    def create_ticket(self, customer_id, message_text, message_id=None):
        counter = self._get_counter("tickets")
        ticket_id = f"TICKET-{counter:05d}"
        now = datetime.now()
        doc = {
            "ticket_id": ticket_id,
            "customer_id": str(customer_id),
            "messages": [{"from": "customer", "text": message_text, "message_id": message_id, "time": now}],
            "status": "open", "created_at": now, "updated_at": now
        }
        self.db.tickets.insert_one(doc)
        logger.info(f"🎫 تیکت جدید: {ticket_id}")
        return ticket_id

    def add_to_ticket(self, ticket_id, sender, text, message_id=None):
        now = datetime.now()
        result = self.db.tickets.update_one(
            {"ticket_id": ticket_id},
            {
                "$push": {"messages": {"from": sender, "text": text, "message_id": message_id, "time": now}},
                "$set": {"status": "admin_replied" if sender == "admin" else "open", "updated_at": now}
            }
        )
        return result.modified_count > 0

    def get_ticket(self, ticket_id):
        return self.db.tickets.find_one({"ticket_id": ticket_id}) or {}

    def get_customer_tickets(self, customer_id):
        docs = self.db.tickets.find({"customer_id": str(customer_id)}).sort("created_at", -1)
        return list(docs)

    def get_open_tickets(self):
        docs = self.db.tickets.find({"status": "open"}).sort("created_at", -1)
        return list(docs)

    def get_all_tickets(self):
        docs = self.db.tickets.find().sort("created_at", -1)
        return {d["ticket_id"]: d for d in docs}

    def close_ticket(self, ticket_id):
        result = self.db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": "closed", "updated_at": datetime.now()}}
        )
        return result.modified_count > 0

    def cleanup_old_tickets(self, days=30):
        cutoff = datetime.now() - timedelta(days=days)
        result = self.db.tickets.delete_many({"status": "closed", "updated_at": {"$lt": cutoff}})
        return result.deleted_count

    # ==================== محصولات ====================

    def get_products(self):
        return list(self.db.products.find().sort("id", 1))

    def get_categories(self):
        docs = self.db.products.distinct("category")
        return [c for c in docs if c]

    def get_product(self, product_id):
        return self.db.products.find_one({"id": product_id}) or {}

    def add_product(self, product: dict) -> bool:
        try:
            self.db.products.insert_one(product)
            return True
        except errors.DuplicateKeyError:
            return False

    def delete_product(self, product_id: str) -> bool:
        result = self.db.products.delete_one({"id": product_id})
        return result.deleted_count > 0

    def update_product(self, product_id: str, updates: dict) -> bool:
        result = self.db.products.update_one({"id": product_id}, {"$set": updates})
        return result.modified_count > 0

    def search_products(self, query: str):
        q = query.lower().strip()
        if not q: return self.get_products()
        regex = f".*{q}.*"
        docs = self.db.products.find({
            "$or": [
                {"name": {"$regex": regex, "$options": "i"}},
                {"description": {"$regex": regex, "$options": "i"}},
                {"category": {"$regex": regex, "$options": "i"}}
            ]
        })
        return list(docs)

    def get_products_by_category(self, category: str):
        return list(self.db.products.find({"category": category}))

    # ==================== سبد خرید ====================

    def get_cart(self, user_id):
        doc = self.db.carts.find_one({"user_id": str(user_id)})
        return doc["items"] if doc else []

    def add_to_cart(self, user_id, product_id: str, quantity: int = 1):
        product = self.get_product(product_id)
        if not product: return False
        result = self.db.carts.update_one(
            {"user_id": str(user_id), "items.product_id": product_id},
            {"$inc": {"items.$.quantity": quantity}},
            upsert=False
        )
        if result.modified_count == 0:
            self.db.carts.update_one(
                {"user_id": str(user_id)},
                {"$push": {"items": {
                    "product_id": product_id,
                    "name": product.get("name", ""),
                    "price": product.get("price", ""),
                    "quantity": quantity,
                    "added_at": datetime.now()
                }}},
                upsert=True
            )
        return True

    def remove_from_cart(self, user_id, product_id: str):
        result = self.db.carts.update_one(
            {"user_id": str(user_id)},
            {"$pull": {"items": {"product_id": product_id}}}
        )
        return result.modified_count > 0

    def clear_cart(self, user_id):
        result = self.db.carts.delete_one({"user_id": str(user_id)})
        return result.deleted_count > 0

    # ==================== سفارشات ====================

    def create_order(self, customer_id, items, total_price, customer_name="", customer_phone="", customer_address="", notes=""):
        counter = self._get_counter("orders")
        order_id = f"ORD-{counter:05d}"
        tracking_code = f"TRK-{datetime.now().strftime('%Y%m')}-{counter:04d}"
        now = datetime.now()
        doc = {
            "order_id": order_id,
            "tracking_code": tracking_code,
            "customer_id": str(customer_id),
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "customer_address": customer_address,
            "notes": notes,
            "items": items,
            "total_price": total_price,
            "status": "pending",
            "status_updates": [{"from": "system", "to": "pending", "time": now, "by": "system"}],
            "created_at": now,
            "updated_at": now
        }
        self.db.orders.insert_one(doc)
        logger.info(f"🛒 سفارش: {order_id} - رهگیری: {tracking_code}")
        return order_id, tracking_code

    def get_customer_orders(self, customer_id):
        docs = self.db.orders.find({"customer_id": str(customer_id)}).sort("created_at", -1)
        return list(docs)

    def get_all_orders(self):
        docs = self.db.orders.find().sort("created_at", -1)
        return {d["order_id"]: d for d in docs}

    def get_order(self, order_id):
        return self.db.orders.find_one({"order_id": order_id}) or {}

    def get_order_by_tracking(self, tracking_code):
        return self.db.orders.find_one({"tracking_code": tracking_code.upper()}) or {}

    def update_order_status(self, order_id, new_status, by="admin"):
        now = datetime.now()
        order = self.db.orders.find_one({"order_id": order_id})
        if not order: return False
        old_status = order.get("status", "")
        result = self.db.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {"status": new_status, "updated_at": now},
                "$push": {"status_updates": {"from": old_status, "to": new_status, "time": now, "by": by}}
            }
        )
        return result.modified_count > 0

    def update_tracking_code(self, order_id, new_code):
        result = self.db.orders.update_one(
            {"order_id": order_id},
            {"$set": {"tracking_code": new_code, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0

    def get_orders_by_status(self, status):
        docs = self.db.orders.find({"status": status}).sort("created_at", -1)
        return list(docs)

    def get_orders_stats(self):
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        results = self.db.orders.aggregate(pipeline)
        stats = {"total": self.db.orders.count_documents({}), "pending": 0, "confirmed": 0, "shipped": 0, "delivered": 0, "cancelled": 0}
        for r in results:
            if r["_id"] in stats:
                stats[r["_id"]] = r["count"]
        return stats

    # ==================== گروه‌ها و کانال‌ها ====================

    def get_all_groups_and_channels(self):
        groups = list(self.db.groups.find({"type": "group"}))
        channels = list(self.db.channels.find({"type": "channel"}))
        return {
            "groups": {g["chat_id"]: g for g in groups},
            "channels": {c["chat_id"]: c for c in channels}
        }

    def get_all_group_chat_ids(self):
        groups = list(self.db.groups.find({}, {"chat_id": 1}))
        channels = list(self.db.channels.find({}, {"chat_id": 1}))
        return [g["chat_id"] for g in groups] + [c["chat_id"] for c in channels]

    def save_group(self, chat_id, title, chat_type):
        key = "channels" if chat_type == "channel" else "groups"
        collection = self.db.channels if chat_type == "channel" else self.db.groups
        collection.update_one(
            {"chat_id": str(chat_id)},
            {"$setOnInsert": {"chat_id": str(chat_id), "title": title or "بدون نام", "type": chat_type, "first_seen": datetime.now()}},
            upsert=True
        )
