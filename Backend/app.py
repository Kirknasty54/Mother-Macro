from flask import Flask, request, jsonify
from backend_common.envdb import db, ensure_user_indexes
from backend_common.security import verify_password, hash_password
from datetime import datetime, timezone
import re

app = Flask(__name__)
ensure_user_indexes()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@app.get("/health")
def health():
    db.client.admin.command("ping")
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
    pw = data.get("password") or ""
    user = db.users.find_one({"email": email})
    if not user or "passwordHash" not in user:
        return jsonify({"ok": False, "msg": "Invalid credentials"}), 401
    if not verify_password(pw, user["passwordHash"]):
        return jsonify({"ok": False, "msg": "Invalid credentials"}), 401
    return jsonify({"ok": True, "user": {
        "id": str(user["_id"]), "email": user["email"], "username": user["username"], "roles": user.get("roles", [])
    }})

@app.post("/auth/register")
def register():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not email or not username or not password:
        return jsonify({"ok": False, "msg": "email, username, and password are required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"ok": False, "msg": "invalid email"}), 400
    if not (3 <= len(username) <= 40):
        return jsonify({"ok": False, "msg": "username must be 3-40 chars"}), 400
    if len(password) < 8:
        return jsonify({"ok": False, "msg": "password must be at least 8 chars"}), 400
    try:
        now = datetime.now(timezone.utc)
        res = db.users.insert_one({
            "email": email,
            "username": username,
            "passwordHash": hash_password(password),
            "roles": ["user"],
            "createdAt": now,
            "updatedAt": now,
            "profile": {"firstName": None, "lastName": None, "avatarUrl": None},
            "meta": {"emailVerified": False, "loginDisabled": False, "provider": "local"}
        })
    except Exception as e:
        # duplicate handling
        if db.users.find_one({"email": email}):
            return jsonify({"ok": False, "msg": "email already in use"}), 409
        if db.users.find_one({"username": username}):
            return jsonify({"ok": False, "msg": "username already in use"}), 409
        return jsonify({"ok": False, "msg": "unable to register"}), 400
    return jsonify({"ok": True, "user": {
        "id": str(res.inserted_id), "email": email, "username": username, "roles": ["user"]
    }}), 201

#i imagine this is going to be what pings the aws agent to generate an actual plan based on data entered from front end
@app.post("/createPlan")
def createplan():
    data = request.get_json(force=True, silent=True) or {}

if __name__ == "__main__":
    app.run(debug=True)
