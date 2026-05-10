"""
اسکریپت انتقال دیتا از JSON به MongoDB
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ['LOG_LEVEL'] = 'ERROR'

from config import DATA_DIR, logger
from pymongo import MongoClient, errors

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "tebahmadi_bot"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Clean existing data
for col in ['admins', 'users', 'products', 'tickets', 'orders', 'carts', 'groups', 'channels', 'counters']:
    db[col].delete_many({})
db.counters.insert_many([
    {"name": "tickets", "value": 0},
    {"name": "orders", "value": 0}
])

# 1. Migrate admins
admins_file = os.path.join(DATA_DIR, "admins.json")
if os.path.exists(admins_file):
    with open(admins_file) as f:
        data = json.load(f)
    for uid in data.get("admins", []):
        try:
            db.admins.insert_one({"user_id": int(uid), "created_at": None})
        except: pass
    print(f"✅ admins: {len(data.get('admins',[]))} migrated")

# 2. Migrate users
users_file = os.path.join(DATA_DIR, "users.json")
if os.path.exists(users_file):
    with open(users_file) as f:
        data = json.load(f)
    count = 0
    for cid, user in data.get("users", {}).items():
        user["chat_id"] = str(cid)
        db.users.update_one({"chat_id": str(cid)}, {"$set": user}, upsert=True)
        count += 1
    print(f"✅ users: {count} migrated")

# 3. Migrate products
products_file = os.path.join(DATA_DIR, "products.json")
if os.path.exists(products_file):
    with open(products_file) as f:
        data = json.load(f)
    for p in data.get("products", []):
        try:
            db.products.insert_one(p)
        except errors.DuplicateKeyError:
            pass
    print(f"✅ products: {len(data.get('products',[]))} migrated")

# 4. Migrate tickets
tickets_file = os.path.join(DATA_DIR, "tickets.json")
if os.path.exists(tickets_file):
    with open(tickets_file) as f:
        data = json.load(f)
    counter = data.get("counter", 0)
    db.counters.update_one({"name": "tickets"}, {"$set": {"value": counter}})
    for tid, ticket in data.get("tickets", {}).items():
        ticket["ticket_id"] = tid
        # Convert ISO strings to datetime
        for msg in ticket.get("messages", []):
            if isinstance(msg.get("time"), str):
                msg["time"] = msg["time"]
        db.tickets.insert_one(ticket)
    print(f"✅ tickets: {len(data.get('tickets',{}))} migrated")

# 5. Migrate orders
orders_file = os.path.join(DATA_DIR, "orders.json")
if os.path.exists(orders_file):
    with open(orders_file) as f:
        data = json.load(f)
    counter = data.get("counter", 0)
    db.counters.update_one({"name": "orders"}, {"$set": {"value": counter}})
    for oid, order in data.get("orders", {}).items():
        order["order_id"] = oid
        db.orders.insert_one(order)
    print(f"✅ orders: {len(data.get('orders',{}))} migrated")

# 6. Migrate carts
carts_file = os.path.join(DATA_DIR, "cart.json")
if os.path.exists(carts_file):
    with open(carts_file) as f:
        data = json.load(f)
    for uid, items in data.get("carts", {}).items():
        db.carts.update_one(
            {"user_id": str(uid)},
            {"$set": {"user_id": str(uid), "items": items}},
            upsert=True
        )
    print(f"✅ carts: {len(data.get('carts',{}))} migrated")

# 7. Migrate groups/channels
groups_file = os.path.join(DATA_DIR, "groups.json")
if os.path.exists(groups_file):
    with open(groups_file) as f:
        data = json.load(f)
    for gid, g in data.get("groups", {}).items():
        g["chat_id"] = gid
        db.groups.update_one({"chat_id": gid}, {"$set": g}, upsert=True)
    for cid, c in data.get("channels", {}).items():
        c["chat_id"] = cid
        db.channels.update_one({"chat_id": cid}, {"$set": c}, upsert=True)
    print(f"✅ groups: {len(data.get('groups',{}))}, channels: {len(data.get('channels',{}))} migrated")

# Verify
print()
print("📊 VERIFICATION:")
for col in ['admins', 'users', 'products', 'tickets', 'orders', 'carts', 'groups', 'channels']:
    count = db[col].count_documents({})
    print(f"   {col}: {count}")

print()
print("🎉 Migration complete!")
