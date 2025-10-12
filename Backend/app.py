# app.py
import json

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
import json  # ensure this is imported (top of file)

# ---- Strands agent helpers (chat-only) ----
def _loads_strict_json(txt: str) -> dict:
    s = str(txt).strip()
    if s.startswith("```"):
        s = s.strip("`")
        nl = s.find("\n")
        if nl > -1 and "{" not in s[:nl]:
            s = s[nl+1:].strip()
    return json.loads(s)

def _mk_agent(model_id: str):
    from strands.agent import Agent
    for kwargs in ({"model": model_id},
                   {"model_id": model_id},
                   {"model": model_id, "provider": "bedrock"},
                   {"model_id": model_id, "provider": "bedrock"}):
        try:
            return Agent(**kwargs)
        except TypeError:
            continue
    return Agent()

def _agent_invoke(agent, system_prompt: str, user_prompt: str, model_id: str):
    try:
        return agent(user_prompt, system_prompt=system_prompt)
    except TypeError:
        pass
    if hasattr(agent, "run"):
        try:
            return agent.run(user_prompt, system_prompt=system_prompt)
        except TypeError:
            pass
    try:
        return agent(user_prompt, system_prompt=system_prompt, model=model_id)
    except TypeError:
        pass
    if hasattr(agent, "run"):
        return agent.run(user_prompt, system_prompt=system_prompt, model=model_id)
    raise RuntimeError("Strands Agent invocation not supported by this version")

def _call_strands_chat(messages: list, mealplan: dict) -> str:
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")

    def brief_mealplan(mp: dict) -> str:
        try:
            days = mp.get("days", [])
            if not isinstance(days, list) or not days:
                return "No mealplan."
            lines = []
            for d in days[:7]:
                if not isinstance(d, dict): continue
                meals = d.get("meals", [])
                names = []
                for m in meals[:4]:
                    if isinstance(m, dict) and isinstance(m.get("name"), str):
                        names.append(m["name"])
                lines.append(f"Day {d.get('day','?')}: {', '.join(names)}")
            return "\n".join(lines) or "No mealplan."
        except Exception:
            return "No mealplan."

    system = (
        "You are a helpful nutrition coach chatbot. "
        "Answer clearly and concisely. If asked for a grocery list, summarize common ingredients. "
        "If asked for swaps, offer 2–3 options with rationale. "
        "If asked for macros, compute/explain using provided info. "
        "Return PLAIN TEXT (no JSON) unless explicitly asked for JSON."
    )

    last_user = ""
    for m in reversed(messages or []):
        if isinstance(m, dict) and (m.get("role") or "").lower() == "user":
            last_user = str(m.get("content", "")).strip()
            if last_user:
                break

    user = (
        f"Mealplan (short):\n{brief_mealplan(mealplan)}\n\n"
        f"User says:\n{last_user or '(no message)'}\n\n"
        "Respond now."
    )

    agent = _mk_agent(model_id)
    raw = _agent_invoke(agent, system_prompt=system, user_prompt=user, model_id=model_id)
    try:
        obj = _loads_strict_json(raw)
        for k in ("reply", "output", "message", "text"):
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return json.dumps(obj)[:2000]
    except Exception:
        return str(raw).strip()


# -------------------- Chat route --------------------
@app.route("/chat", methods=["POST"])
@require_auth
def chat():
    """
    Accepts: { messages: [{role, content}] | string, mealplan: {...} | string }
    Returns: { ok: true, reply: string, debug?: {...} }
    """
    try:
        # ----- super defensive parsing -----
        def as_dict(x):
            if isinstance(x, dict): return x
            if isinstance(x, str):
                try:
                    j = json.loads(x);
                    return j if isinstance(j, dict) else {}
                except Exception:
                    return {}
            return {}

        def as_list(x):
            if isinstance(x, list): return x
            if isinstance(x, str):
                try:
                    j = json.loads(x);
                    return j if isinstance(j, list) else []
                except Exception:
                    return []
            return []

        data = request.get_json(silent=True)
        if isinstance(data, str):
            try: data = json.loads(data)
            except Exception: data = {}
        if not isinstance(data, dict): data = {}

        msgs_in  = as_list(data.get("messages"))
        messages = []
        for m in msgs_in:
            if isinstance(m, dict):
                role = str(m.get("role", "")).strip().lower()
                content = m.get("content", "")
                if isinstance(content, (int, float)): content = str(content)
                if isinstance(content, str):
                    messages.append({"role": role, "content": content})
            elif isinstance(m, str) and m.strip():
                messages.append({"role": "user", "content": m.strip()})

        mealplan = as_dict(data.get("mealplan"))

        # ----- Strands Agent first (toggle with USE_STRANDS_CHAT) -----
        if os.getenv("USE_STRANDS_CHAT", "1") not in ("0", "false", "False"):
            try:
                agent_reply = _call_strands_chat(messages, mealplan)
                if isinstance(agent_reply, str) and agent_reply.strip():
                    return jsonify({"ok": True, "reply": agent_reply, "debug": {"source": "strands"}})
            except Exception as e:
                print("Strands chat failed:", e)

        # ----- fallback simple reply so UI never breaks -----
        reply = "I can help with your meal plan chat. Ask for grocery lists, swaps, or macros per meal."
        return jsonify({"ok": True, "reply": reply, "debug": {"source": "fallback"}})

    except Exception as e:
        return jsonify({"ok": False, "msg": f"chat error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
