from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import bcrypt

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "appdb")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
app = Flask(__name__)

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

if __name__ == '__main__':
    app.run()

@app.get("/health")
def health():
    client.admin.command("ping")
    return {"ok": True}

@app.get("/users")
def list_users():
    docs = list(db.users.find({}, {"passwordHash": 0}).limit(10))
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify(docs)

@app.post("/auth/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = db.users.find_one({"email": email})
    if not user or "passwordHash" not in user:
        return jsonify({"ok": False, "msg": "Invalid credentials"}), 401

    ok = bcrypt.checkpw(password.encode(), user["passwordHash"].encode())
    if not ok:
        return jsonify({"ok": False, "msg": "Invalid credentials"}), 401

    # Dev-only response. In a real app, return a JWT/session.
    return jsonify({
        "ok": True,
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "username": user["username"],
            "roles": user.get("roles", []),
        }
    })

