#!/usr/bin/env python3
"""
Secure MongoDB Atlas seeder for dummy user/login data.

What it does
- Connects to your Atlas cluster using MONGODB_URI from .env
- Creates unique indexes on email and username (idempotent)
- Optionally sets a JSON Schema validator to enforce basic structure
- Inserts N fake users with Bcrypt-hashed passwords (no plaintext stored)
- Can also insert a few fixed test accounts you specify

Usage
  1) cp .env.example .env  # edit values
  2) pip install -r requirements.txt
  3) python seed_users.py --count 50 --with-fixed

Notes
- Never commit your real .env to git. Add ".env" to your .gitignore.
- If you get auth/allowlist errors, add your IP in Atlas Network Access and create a DB user with proper roles.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone

from bson import ObjectId
from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient, ASCENDING, errors
import bcrypt

fake = Faker()

def load_env():
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "appdb")
    coll_name = os.getenv("COLLECTION_NAME", "users")
    if not mongo_uri:
        print("ERROR: MONGODB_URI not set. Create a .env file (see .env.example).", file=sys.stderr)
        sys.exit(1)
    return mongo_uri, db_name, coll_name

def get_client(mongo_uri: str) -> MongoClient:
    # MongoClient will use SRV and TLS if provided in the URI from Atlas
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=8000)
        # Force a ping to validate the connection
        client.admin.command("ping")
        return client
    except errors.PyMongoError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(2)

def ensure_indexes_and_schema(coll):
    # Unique indexes
    coll.create_index([("email", ASCENDING)], name="uniq_email", unique=True, background=True)
    coll.create_index([("username", ASCENDING)], name="uniq_username", unique=True, background=True)
    coll.create_index([("createdAt", ASCENDING)], name="createdAt_idx", background=True)

    # Optional JSON Schema validator (basic example). Skip if permissions disallow collMod.
    schema = {
        "bsonType": "object",
        "required": ["email", "username", "passwordHash", "roles", "createdAt"],
        "properties": {
            "email": {"bsonType": "string", "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
            "username": {"bsonType": "string", "minLength": 3, "maxLength": 40},
            "passwordHash": {"bsonType": "string", "minLength": 20},
            "roles": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "minItems": 1
            },
            "createdAt": {"bsonType": "date"},
            "updatedAt": {"bsonType": "date"},
            "profile": {
                "bsonType": "object",
                "properties": {
                    "firstName": {"bsonType": "string"},
                    "lastName": {"bsonType": "string"},
                    "avatarUrl": {"bsonType": "string"},
                }
            }
        },
        "additionalProperties": True
    }

    try:
        coll.database.command({
            "collMod": coll.name,
            "validator": {"$jsonSchema": schema},
            "validationLevel": "moderate"
        })
    except errors.OperationFailure as e:
        # If collection doesn't exist yet, create with validator
        if "NamespaceNotFound" in str(e):
            coll.database.create_collection(
                coll.name,
                validator={"$jsonSchema": schema},
                validationLevel="moderate"
            )
        else:
            # Not fatal—indexing still protects uniqueness
            print(f"Schema set skipped: {e}", file=sys.stderr)

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

def make_user() -> dict:
    first = fake.first_name()
    last = fake.last_name()
    username = (first[0] + last).lower() + str(fake.random_int(10, 99))
    email = f"{first.lower()}.{last.lower()}{fake.random_int(100,999)}@example.com"
    password_plain = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    user = {
        "_id": ObjectId(),
        "email": email,
        "username": username,
        "passwordHash": hash_password(password_plain),
        # You might log or return the plaintext ONLY during seeding if you need to test login flows.
        # DO NOT store plaintext in the DB.
        "roles": ["user"],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
        "profile": {
            "firstName": first,
            "lastName": last,
            "avatarUrl": f"https://i.pravatar.cc/150?u={username}"
        },
        "meta": {
            "emailVerified": False,
            "loginDisabled": False,
            "provider": "local"
        }
    }
    return user, password_plain

def fixed_test_accounts():
    # You can log these passwords to console for testing (do NOT store in DB).
    accounts = [
        ("test.user1@example.com", "testuser1", "Passw0rd!234"),
        ("test.user2@example.com", "testuser2", "Passw0rd!234"),
        ("admin@example.com", "adminuser", "Admin!23456"),
    ]
    docs = []
    creds = []
    for email, username, pw in accounts:
        docs.append({
            "_id": ObjectId(),
            "email": email,
            "username": username,
            "passwordHash": hash_password(pw),
            "roles": ["admin"] if "admin" in username else ["user"],
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "profile": {"firstName": username.split('user')[0] or "Test", "lastName": "Account"},
            "meta": {"emailVerified": False, "loginDisabled": False, "provider": "local"}
        })
        creds.append((email, username, pw))
    return docs, creds

def main():
    parser = argparse.ArgumentParser(description="Seed MongoDB Atlas with dummy users.")
    parser.add_argument("--count", type=int, default=20, help="How many random users to create (default: 20).")
    parser.add_argument("--with-fixed", action="store_true", help="Also insert fixed test accounts.")
    parser.add_argument("--drop", action="store_true", help="Drop the collection before seeding (careful).")
    args = parser.parse_args()

    mongo_uri, db_name, coll_name = load_env()
    client = get_client(mongo_uri)
    db = client[db_name]
    coll = db[coll_name]

    if args.drop:
        try:
            coll.drop()
            print(f"Dropped collection '{db_name}.{coll_name}'")
            time.sleep(0.5)
        except errors.PyMongoError as e:
            print(f"Drop failed (continuing): {e}", file=sys.stderr)

    ensure_indexes_and_schema(coll)

    # Build docs
    docs = []
    plain_creds = []  # Keep only in memory; printed once for testing convenience
    if args.with_fixed:
        fixed_docs, fixed_creds = fixed_test_accounts()
        docs.extend(fixed_docs)
        plain_creds.extend(fixed_creds)

    for _ in range(args.count):
        u, pw = make_user()
        docs.append(u)
        plain_creds.append((u["email"], u["username"], pw))

    # Insert
    try:
        if docs:
            result = coll.insert_many(docs, ordered=False)
            print(f"Inserted {len(result.inserted_ids)} users into {db_name}.{coll_name}")
    except errors.BulkWriteError as bwe:
        # Likely duplicate key errors from unique indexes if re-running with fixed users
        print(f"Bulk write encountered issues: {bwe.details.get('writeErrors', [])}", file=sys.stderr)

    # Print plaintext credentials for testing ONLY (do not log in production)
    print("\n--- Temporary Test Credentials (NOT stored in DB) ---")
    for (email, username, pw) in plain_creds[:10]:  # show up to 10 to avoid clutter
        print(f"email={email} | username={username} | password={pw}")
    if len(plain_creds) > 10:
        print(f"... and {len(plain_creds)-10} more.")

    print("\nDone.")
    client.close()

if __name__ == "__main__":
    main()
