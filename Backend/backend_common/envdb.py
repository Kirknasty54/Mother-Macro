# backend_common/envdb.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

load_dotenv()  # loads .env once when imported

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "appdb")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI not set in .env")

_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=8000)
_client.admin.command("ping")  # fail fast if bad URI

db = _client[DB_NAME]

def ensure_user_indexes():
    db.users.create_index([("email", ASCENDING)], unique=True, name="uniq_email")
    db.users.create_index([("username", ASCENDING)], unique=True, name="uniq_username")
    db.users.create_index([("createdAt", ASCENDING)], name="createdAt_idx")
