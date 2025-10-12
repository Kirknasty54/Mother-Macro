#!/usr/bin/env python3
"""
Seed script: drop old users, insert fixed test accounts, and save plaintext creds to test-creds.txt

Usage (recommended, runs locally):
  # create/activate venv then install deps:
  # python -m venv .venv
  # source .venv/bin/activate
  # pip install -r requirements.txt

  # Run: drop the collection and insert only fixed accounts (and write creds file)
  python seed_users_writecreds.py --drop --with-fixed

Notes:
- This writes plaintext test credentials to test-creds.txt in the same folder.
  The file is created with permission 0o600 (owner read/write only).
- Do NOT commit test-creds.txt or .env to source control.
"""
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, errors
import bcrypt

# ----- CONFIG -----
CREDS_FILENAME = "test-creds.txt"

# ----- Helpers -----
def load_env():
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI")
    # support building from pieces if user set them instead
    if not mongo_uri:
        user = os.getenv("MONGODB_USER")
        pw = os.getenv("MONGODB_PASSWORD")
        host = os.getenv("MONGODB_HOST")
        appname = os.getenv("MONGODB_APPNAME", "SeedScript")
        if user and pw and host:
            mongo_uri = f"mongodb+srv://{quote_plus(user)}:{quote_plus(pw)}@{host}/?retryWrites=true&w=majority&appName={appname}"
    db_name = os.getenv("DB_NAME", "appdb")
    coll_name = os.getenv("COLLECTION_NAME", "users")
    if not mongo_uri:
        print("ERROR: MONGODB_URI not set. Create a .env file (see .env.example).", file=sys.stderr)
        sys.exit(1)
    return mongo_uri, db_name, coll_name

def get_client(mongo_uri: str) -> MongoClient:
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=8000)
        client.admin.command("ping")
        return client
    except errors.PyMongoError as e:
        print(f"Connection error: {e}")
        sys.exit(2)

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

def fixed_test_accounts():
    accounts = [
        ("test.user1@example.com", "testuser1", "Passw0rd!234"),
        ("test.user2@example.com", "testuser2", "Passw0rd!234"),
        ("admin@example.com", "adminuser", "Admin!23456"),
    ]
    docs = []
    creds = []
    now = datetime.now(timezone.utc)
    for email, username, pw in accounts:
        docs.append({
            "_id": ObjectId(),
            "email": email,
            "username": username,
            "passwordHash": hash_password(pw),
            "roles": ["admin"] if "admin" in username else ["user"],
            "createdAt": now,
            "updatedAt": now,
            "profile": {"firstName": username.split('user')[0] or "Test", "lastName": "Account"},
            "meta": {"emailVerified": False, "loginDisabled": False, "provider": "local"},
            "meals": ""
        })
        creds.append((email, username, pw))
    return docs, creds

def ensure_indexes(coll):
    coll.create_index([("email", ASCENDING)], name="uniq_email", unique=True, background=True)
    coll.create_index([("username", ASCENDING)], name="uniq_username", unique=True, background=True)

def write_creds_file(creds, path: Path):
    # write file with owner-only permissions
    content_lines = []
    content_lines.append("# test-creds.txt - temporary test credentials (delete when done)")
    content_lines.append(f"# generated: {datetime.now(timezone.utc).isoformat()}")
    content_lines.append("")
    for email, username, pw in creds:
        content_lines.append(f"email={email} | username={username} | password={pw}")
    txt = "\n".join(content_lines) + "\n"
    # atomic write
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(txt)
    # set file permissions to 0o600
    os.chmod(tmp, 0o600)
    tmp.replace(path)

# ----- Main -----
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed MongoDB with fixed test accounts and persist creds file.")
    parser.add_argument("--with-fixed", action="store_true", help="Insert fixed known test accounts.")
    parser.add_argument("--drop", action="store_true", help="Drop the collection before inserting (irreversible).")
    args = parser.parse_args()

    mongo_uri, db_name, coll_name = load_env()
    client = get_client(mongo_uri)
    db = client[db_name]
    coll = db[coll_name]

    if args.drop:
        try:
            coll.drop()
            print(f"Dropped collection '{db_name}.{coll_name}'.")
            time.sleep(0.3)
        except errors.PyMongoError as e:
            print(f"Drop failed (continuing): {e}")

    ensure_indexes(coll)

    inserted_docs = []
    creds_to_save = []

    if args.with_fixed:
        fixed_docs, fixed_creds = fixed_test_accounts()
        try:
            res = coll.insert_many(fixed_docs, ordered=False)
            inserted_docs.extend(res.inserted_ids)
            creds_to_save.extend(fixed_creds)
        except errors.BulkWriteError as bwe:
            # some duplicates may occur if you re-run w/out drop
            print("Bulk write issues:", bwe.details.get("writeErrors", []))
            # still attempt to collect all fixed creds to write them out
            creds_to_save.extend(fixed_creds)

    # write the creds file if any creds were generated
    if creds_to_save:
        out_path = Path.cwd() / CREDS_FILENAME
        write_creds_file(creds_to_save, out_path)
        print(f"Wrote {len(creds_to_save)} test credentials to {out_path} (mode 600).")

    # final counts and info
    total = coll.count_documents({})
    print(f"Total documents in {db_name}.{coll_name}: {total}")
    client.close()

if __name__ == "__main__":
    main()
