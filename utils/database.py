"""
دیتابیس MongoDB - جایگزین JSON
API کاملاً مشابه نسخه قبلی برای سازگاری با هندلرها
"""
import os
from datetime import datetime, timedelta
from pymongo import MongoClient, errors
from config import MONGO_URI, MONGO_DB_NAME, SUPER_ADMIN_ID, logger


class Database:
    """مدیریت دیتابیس MongoDB - توابع استاتیک"""

    _client = None
    _db = None

    @classmethod
    def _get_db(cls):
        if cls._db is None:
            try:
                cls._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                cls._db = cls._client[MONGO_DB_NAME]
                cls._client.server_info()
                cls._ensure_indexes()
            except Exception as e:
                logger.error(f"❌ MongoDB: {e}")
                raise
        return cls._db

    @classmethod
    def _ensure_indexes(cls):
        db = cls._get_db()
        for col, field in [("users","chat_id"),("orders","order_id"),("orders","tracking_code"),
                          ("tickets","ticket_id"),("products","id"),("carts","user_id"),
                          ("counters","name")]:
            try: db[col].create_index(field, unique=True)
            except: pass

    @classmethod
    def _counter(cls, name):
        db = cls._get_db()
        r = db.counters.find_one_and_update(
            {"name": name}, {"$inc": {"value": 1}},
            upsert=True, return_document=True
        )
        return r["value"]

    # ==================== ادمین‌ها ====================

    @classmethod
    def get_admins_list(cls):
        return [d["user_id"] for d in cls._get_db().admins.find({}, {"user_id":1,"_id":0})]

    @classmethod
    def is_admin(cls, user_id):
        try:
            uid = int(user_id) if not isinstance(user_id, int) else user_id
            return uid == SUPER_ADMIN_ID or cls._get_db().admins.find_one({"user_id": uid}) is not None
        except: return False

    @classmethod
    def is_super_admin(cls, user_id):
        try:
            uid = int(user_id) if not isinstance(user_id, int) else user_id
            return uid == SUPER_ADMIN_ID and SUPER_ADMIN_ID != 0
        except: return False

    @classmethod
    def add_admin(cls, user_id):
        try:
            uid = int(user_id) if not isinstance(user_id, int) else user_id
            cls._get_db().admins.update_one({"user_id": uid}, {"$setOnInsert": {"user_id": uid}}, upsert=True)
            return True
        except: return False

    @classmethod
    def remove_admin(cls, user_id):
        try:
            return cls._get_db().admins.delete_one({"user_id": int(user_id)}).deleted_count > 0
        except: return False

    @classmethod
    def get_all_admin_ids(cls):
        admins = cls.get_admins_list()
        if SUPER_ADMIN_ID and SUPER_ADMIN_ID not in admins:
            admins.insert(0, SUPER_ADMIN_ID)
        return admins

    # ==================== کاربران ====================

    @classmethod
    def register_user(cls, chat_id, user_info):
        db = cls._get_db()
        now = datetime.now().isoformat()
        db.users.update_one(
            {"chat_id": str(chat_id)},
            {
                "$setOnInsert": {
                    "chat_id": str(chat_id), "first_name": user_info.get("first_name",""),
                    "last_name": user_info.get("last_name",""), "username": user_info.get("username",""),
                    "phone": user_info.get("phone",""), "first_seen": now, "is_blocked": False
                },
                "$set": {"last_seen": now},
                "$inc": {"messages_count": 1}
            }, upsert=True
        )
        updates = {}
        if user_info.get("first_name"): updates["first_name"] = user_info["first_name"]
        if user_info.get("last_name"): updates["last_name"] = user_info["last_name"]
        if user_info.get("username"): updates["username"] = user_info["username"]
        if updates: db.users.update_one({"chat_id": str(chat_id)}, {"$set": updates})
        return True

    @classmethod
    def get_all_users(cls):
        return {d.get("chat_id", ""): d for d in cls._get_db().users.find().sort("last_seen", -1)}

    @classmethod
    def get_all_chat_ids(cls):
        return [d.get("chat_id", "") for d in cls._get_db().users.find({"is_blocked": {"$ne": True}}, {"chat_id":1}) if d.get("chat_id")]

    @classmethod
    def get_user_count(cls):
        return cls._get_db().users.count_documents({})

    @classmethod
    def get_user_info(cls, chat_id):
        return cls._get_db().users.find_one({"chat_id": str(chat_id)}) or {}

    @classmethod
    def block_user(cls, chat_id):
        return cls._get_db().users.update_one({"chat_id": str(chat_id)}, {"$set":{"is_blocked":True}}).modified_count > 0

    @classmethod
    def unblock_user(cls, chat_id):
        return cls._get_db().users.update_one({"chat_id": str(chat_id)}, {"$set":{"is_blocked":False}}).modified_count > 0

    @classmethod
    def get_user_orders_count(cls, chat_id):
        return cls._get_db().orders.count_documents({"customer_id": str(chat_id)})

    # ==================== تیکت‌ها ====================

    @classmethod
    def create_ticket(cls, customer_id, message_text, message_id=None):
        db = cls._get_db()
        counter = cls._counter("tickets")
        tid = f"TICKET-{counter:05d}"
        now = datetime.now().isoformat()
        db.tickets.insert_one({
            "ticket_id": tid, "customer_id": str(customer_id),
            "messages": [{"from":"customer","text":message_text,"message_id":message_id,"time":now}],
            "status": "open", "created_at": now, "updated_at": now
        })
        logger.info(f"🎫 تیکت: {tid}")
        return tid

    @classmethod
    def add_to_ticket(cls, ticket_id, sender, text, message_id=None):
        now = datetime.now().isoformat()
        r = cls._get_db().tickets.update_one(
            {"ticket_id": ticket_id},
            {"$push": {"messages": {"from":sender,"text":text,"message_id":message_id,"time":now}},
             "$set": {"status":"admin_replied" if sender=="admin" else "open", "updated_at":now}}
        )
        return r.modified_count > 0

    @classmethod
    def get_ticket(cls, ticket_id):
        return cls._get_db().tickets.find_one({"ticket_id": ticket_id}) or {}

    @classmethod
    def get_customer_tickets(cls, customer_id):
        return list(cls._get_db().tickets.find({"customer_id": str(customer_id)}).sort("created_at",-1))

    @classmethod
    def get_open_tickets(cls):
        return list(cls._get_db().tickets.find({"status": "open"}).sort("created_at",-1))

    @classmethod
    def get_all_tickets(cls):
        return {d["ticket_id"]: d for d in cls._get_db().tickets.find().sort("created_at",-1)}

    @classmethod
    def close_ticket(cls, ticket_id):
        r = cls._get_db().tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status":"closed", "updated_at": datetime.now().isoformat()}}
        )
        return r.modified_count > 0

    @classmethod
    def cleanup_old_tickets(cls, days=30):
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        r = cls._get_db().tickets.delete_many({"status":"closed","updated_at":{"$lt":cutoff}})
        return r.deleted_count

    # ==================== محصولات ====================

    @classmethod
    def get_products(cls):
        return list(cls._get_db().products.find().sort("id",1))

    @classmethod
    def get_categories(cls):
        return [c for c in cls._get_db().products.distinct("category") if c]

    @classmethod
    def get_product(cls, product_id):
        return cls._get_db().products.find_one({"id": product_id}) or {}

    @classmethod
    def add_product(cls, product):
        try:
            cls._get_db().products.insert_one(product)
            return True
        except errors.DuplicateKeyError:
            return False

    @classmethod
    def delete_product(cls, product_id):
        return cls._get_db().products.delete_one({"id": product_id}).deleted_count > 0

    @classmethod
    def update_product(cls, product_id, updates):
        r = cls._get_db().products.update_one({"id": product_id}, {"$set": updates})
        return r.modified_count > 0

    @classmethod
    def search_products(cls, query):
        q = query.strip()
        if not q: return cls.get_products()
        import re as re_m
        pat = f".*{re_m.escape(q)}.*"
        docs = cls._get_db().products.find({
            "$or": [
                {"name": {"$regex": pat, "$options": "i"}},
                {"description": {"$regex": pat, "$options": "i"}},
                {"category": {"$regex": pat, "$options": "i"}}
            ]
        })
        return list(docs)

    @classmethod
    def get_products_by_category(cls, category):
        return list(cls._get_db().products.find({"category": category}))

    # ==================== سبد خرید ====================

    @classmethod
    def get_cart(cls, user_id):
        doc = cls._get_db().carts.find_one({"user_id": str(user_id)})
        return doc["items"] if doc else []

    @classmethod
    def add_to_cart(cls, user_id, product_id, quantity=1):
        p = cls.get_product(product_id)
        if not p: return False
        db = cls._get_db()
        r = db.carts.update_one(
            {"user_id": str(user_id), "items.product_id": product_id},
            {"$inc": {"items.$.quantity": quantity}}
        )
        if r.modified_count == 0:
            db.carts.update_one(
                {"user_id": str(user_id)},
                {"$push": {"items": {"product_id":product_id,"name":p.get("name",""),
                    "price":p.get("price",""),"quantity":quantity,"added_at":datetime.now().isoformat()}}},
                upsert=True
            )
        return True

    @classmethod
    def remove_from_cart(cls, user_id, product_id):
        r = cls._get_db().carts.update_one(
            {"user_id": str(user_id)},
            {"$pull": {"items": {"product_id": product_id}}}
        )
        return r.modified_count > 0

    @classmethod
    def clear_cart(cls, user_id):
        return cls._get_db().carts.delete_one({"user_id": str(user_id)}).deleted_count > 0

    # ==================== سفارشات ====================

    @classmethod
    def create_order(cls, customer_id, items, total_price, customer_name="", customer_phone="", customer_address="", notes=""):
        db = cls._get_db()
        counter = cls._counter("orders")
        oid = f"ORD-{counter:05d}"
        trk = f"TRK-{datetime.now().strftime('%Y%m')}-{counter:04d}"
        now = datetime.now().isoformat()
        db.orders.insert_one({
            "order_id": oid, "tracking_code": trk,
            "customer_id": str(customer_id), "customer_name": customer_name,
            "customer_phone": customer_phone, "customer_address": customer_address,
            "notes": notes, "items": items, "total_price": total_price,
            "status": "pending",
            "status_updates": [{"from":"system","to":"pending","time":now,"by":"system"}],
            "created_at": now, "updated_at": now
        })
        logger.info(f"🛒 {oid} - رهگیری: {trk}")
        return oid, trk

    @classmethod
    def get_customer_orders(cls, customer_id):
        return list(cls._get_db().orders.find({"customer_id": str(customer_id)}).sort("created_at",-1))

    @classmethod
    def get_all_orders(cls):
        return {d["order_id"]: d for d in cls._get_db().orders.find().sort("created_at",-1)}

    @classmethod
    def get_order(cls, order_id):
        return cls._get_db().orders.find_one({"order_id": order_id}) or {}

    @classmethod
    def get_order_by_tracking(cls, tracking_code):
        return cls._get_db().orders.find_one({"tracking_code": tracking_code.upper()}) or {}

    @classmethod
    def update_order_status(cls, order_id, new_status, by="admin"):
        now = datetime.now().isoformat()
        order = cls.get_order(order_id)
        if not order: return False
        r = cls._get_db().orders.update_one(
            {"order_id": order_id},
            {"$set": {"status": new_status, "updated_at": now},
             "$push": {"status_updates": {"from":order.get("status",""),"to":new_status,"time":now,"by":by}}}
        )
        return r.modified_count > 0

    @classmethod
    def update_tracking_code(cls, order_id, new_code):
        r = cls._get_db().orders.update_one(
            {"order_id": order_id},
            {"$set": {"tracking_code": new_code, "updated_at": datetime.now().isoformat()}}
        )
        return r.modified_count > 0

    @classmethod
    def get_orders_by_status(cls, status):
        return list(cls._get_db().orders.find({"status": status}).sort("created_at",-1))

    @classmethod
    def get_orders_stats(cls):
        db = cls._get_db()
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        stats = {"total": db.orders.count_documents({}), "pending":0, "confirmed":0, "shipped":0, "delivered":0, "cancelled":0}
        for r in db.orders.aggregate(pipeline):
            if r["_id"] in stats: stats[r["_id"]] = r["count"]
        return stats

    # ==================== گروه‌ها و کانال‌ها ====================

    @classmethod
    def get_all_groups_and_channels(cls):
        db = cls._get_db()
        groups = {g["chat_id"]: g for g in db.groups.find({})}
        channels = {c["chat_id"]: c for c in db.channels.find({})}
        return {"groups": groups, "channels": channels}

    @classmethod
    def get_all_group_chat_ids(cls):
        return [g["chat_id"] for g in cls._get_db().groups.find({},{"chat_id":1})] + \
               [c["chat_id"] for c in cls._get_db().channels.find({},{"chat_id":1})]

    @classmethod
    def save_group(cls, chat_id, title, chat_type):
        col = cls._get_db().channels if chat_type == "channel" else cls._get_db().groups
        col.update_one(
            {"chat_id": str(chat_id)},
            {"$setOnInsert": {"chat_id": str(chat_id), "title": title or "بدون نام",
              "type": chat_type, "first_seen": datetime.now().isoformat()}},
            upsert=True
        )
