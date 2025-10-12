# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone
from functools import wraps
import re
# Shared helpers (make sure these files exist)
from backend_common.envdb import db, ensure_user_indexes
from backend_common.security import hash_password, verify_password
from backend_common.jwt_tools import mint_access_and_refresh, verify_token
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name(".env"))
except Exception:
    pass

# If you saved the prefs/meal routes as routes_prefs_meals.py next to this file:
from routes_prefs_meals import bp as prefs_bp
app = Flask(__name__)
if "prefs_meals" not in app.blueprints:
    app.register_blueprint(prefs_bp)  # exposes /preferences, /mealplans/generate
# DEV: allow your Vite origins (localhost and 127.0.0.1) and Authorization header
CORS(
    app,
    resources={r"/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,  # you're using Bearer tokens, not cookies
    }},
)

ensure_user_indexes()  # creates unique indexes for users once at startup

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def public_user(u):
    return {
        "id": str(u["_id"]),
        "email": u["email"],
        "username": u["username"],
        "roles": u.get("roles", []),
    }

@app.get("/health")
def health():
    db.client.admin.command("ping")
    return {"ok": True}

@app.post("/auth/register")
def register():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not email or not username or not password:
        return jsonify({"ok": False, "msg": "email, username, and password required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"ok": False, "msg": "invalid email"}), 400
    if not (3 <= len(username) <= 40):
        return jsonify({"ok": False, "msg": "username must be 3–40 chars"}), 400
    if len(password) < 8:
        return jsonify({"ok": False, "msg": "password must be at least 8 chars"}), 400

    if db.users.find_one({"email": email}):
        return jsonify({"ok": False, "msg": "email already in use"}), 409
    if db.users.find_one({"username": username}):
        return jsonify({"ok": False, "msg": "username already in use"}), 409

    now = datetime.now(timezone.utc)
    user = {
        "email": email,
        "username": username,
        "passwordHash": hash_password(password),
        "roles": ["user"],
        "createdAt": now,
        "updatedAt": now,
        "profile": {"firstName": None, "lastName": None, "avatarUrl": None},
        "meta": {"emailVerified": False, "loginDisabled": False, "provider": "local"},
    }
    res = db.users.insert_one(user)
    user["_id"] = res.inserted_id

    tokens = mint_access_and_refresh(user)
    return jsonify({"ok": True, "user": public_user(user), **tokens}), 201

@app.post("/auth/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    pw = data.get("password") or ""

    user = db.users.find_one({"email": email})
    if not user or "passwordHash" not in user:
        return jsonify({"ok": False, "msg": "invalid credentials"}), 401
    if not verify_password(pw, user["passwordHash"]):
        return jsonify({"ok": False, "msg": "invalid credentials"}), 401

    tokens = mint_access_and_refresh(user)
    return jsonify({"ok": True, "user": public_user(user), **tokens})

@app.post("/auth/refresh")
def refresh():
    data = request.get_json(force=True, silent=True) or {}
    token = data.get("refresh_token") or ""
    try:
        claims = verify_token(token)
        if claims.get("typ") != "refresh":
            return jsonify({"ok": False, "msg": "wrong token type"}), 400
        user = db.users.find_one({"email": claims.get("email")})
        if not user:
            return jsonify({"ok": False, "msg": "user not found"}), 404
        tokens = mint_access_and_refresh(user)
        return jsonify({"ok": True, **tokens})
    except Exception:
        return jsonify({"ok": False, "msg": "invalid or expired refresh token"}), 401

# --- Auth decorator for any protected route ---
def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.lower().startswith("bearer "):
            return jsonify({"ok": False, "msg": "missing bearer token"}), 401
        token = auth.split(" ", 1)[1].strip()
        try:
            claims = verify_token(token)
            request.user = claims
        except Exception:
            return jsonify({"ok": False, "msg": "invalid or expired token"}), 401
        return fn(*args, **kwargs)
    return wrapper

@app.get("/me")
@require_auth
def me():
    return jsonify({"ok": True, "claims": getattr(request, "user", {})})

if __name__ == "__main__":
    app.run(debug=True)
