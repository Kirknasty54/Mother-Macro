# routes_prefs_meals.py
from flask import Blueprint, request, jsonify
from typing import Any, Dict, List
from bson import ObjectId
import os, json, random, traceback

from backend_common.envdb import db
from backend_common.jwt_tools import verify_token

bp = Blueprint("prefs_meals", __name__)

# -------------------- auth + helpers --------------------

def _claims_from_auth_header() -> Dict[str, Any]:
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        raise ValueError("missing bearer token")
    token = auth.split(" ", 1)[1].strip()
    return verify_token(token)

def _oid(s: str) -> ObjectId:
    try:
        return ObjectId(s)
    except Exception:
        # impossible placeholder to avoid crashes
        return ObjectId("000000000000000000000000")

def _loads_strict_json(txt: str) -> dict:
    """Strip code fences if present and parse JSON strictly."""
    s = str(txt).strip()
    if s.startswith("```"):
        s = s.strip("`")
        nl = s.find("\n")
        if nl > -1 and "{" not in s[:nl]:
            s = s[nl+1:].strip()
    return json.loads(s)

# ---------- VERSION-TOLERANT STRANDS HELPERS ----------


def _mk_agent(model_id: str, strands=None):
    """
    Create a Strands Agent that uses Bedrock in a compatible way.
    """
    import os
    import boto3
    from strands.agent import Agent

    # Force the region
    region = os.getenv("AWS_REGION", "us-east-1")
    os.environ['AWS_DEFAULT_REGION'] = region

    # Try different initialization approaches
    # Priority: Use explicit boto3 client configuration
    try:
        # Create boto3 bedrock-runtime client explicitly
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=region
        )

        # Try to pass the client to Strands if it accepts it
        return Agent(
            model=model_id,
            provider="bedrock",
            client=bedrock_client  # Some versions accept this
        )
    except (TypeError, Exception) as e:
        print(f"Approach 1 failed: {e}")

    # Fallback approaches
    for kwargs in (
            {"model": model_id, "provider": "bedrock"},
            {"model_id": model_id, "provider": "bedrock"},
            {"model": model_id},
            {"model_id": model_id},
    ):
        try:
            agent = Agent(**kwargs)
            # Force region on the agent if possible
            if hasattr(agent, 'client') and hasattr(agent.client, 'meta'):
                agent.client.meta.region_name = region
            return agent
        except TypeError:
            continue

    return Agent()  # last resortt

def _agent_invoke(agent, system_prompt: str, user_prompt: str, model_id: str):
    """
    Call the agent using whichever interface the installed version supports.
    Tries (in order):
      agent(user_prompt, system_prompt=...)
      agent.run(user_prompt, system_prompt=...)
      agent(user_prompt, system_prompt=..., model=model_id)
      agent.run(user_prompt, system_prompt=..., model=model_id)
    """
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
    raise RuntimeError("Strands Agent invocation method not supported by this version")


def _call_strands_mealplan(prefs: dict) -> dict:
    """Use Strands against Bedrock, tolerant to API differences."""
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

    # DEBUG: Print what we're actually using
    print(f"DEBUG: Using model_id: {model_id}")
    print(f"DEBUG: AWS_REGION: {os.getenv('AWS_REGION')}")
    print(f"DEBUG: AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID', 'NOT SET')[:20]}...")

    calorie_target = int(prefs.get("calorie_target") or 2200)
    meals_per_day = int(prefs.get("meals_per_day") or 3)
    diet = prefs.get("diet") or "balanced"
    excludes = ", ".join(map(str, prefs.get("exclude_ingredients", []))) or "none"

    # ... rest of the function stays the same ...
    system = (
        "You are a nutrition planner. Respond with STRICT JSON ONLY. "
        "No markdown, no code fences, no explanations."
    )
    user = f"""
Create a 7-day meal plan with {meals_per_day} meals per day for a {diet} diet.
Daily calorie target: {calorie_target} kcal.
Avoid these ingredients if present: {excludes}.

Return EXACTLY this JSON schema:
{{
  "days": [
    {{
      "day": 1,
      "meals": [
        {{
          "name": "string",
          "calories": number,
          "protein_g": number,
          "carbs_g": number,
          "fat_g": number,
          "recipe_text": "short steps"
        }}
      ]
    }},
    ... include days 2..7 ...
  ]
}}
Only output valid JSON (no comments, no trailing commas).
"""
    agent = _mk_agent(model_id)
    raw = _agent_invoke(agent, system_prompt=system, user_prompt=user, model_id=model_id)
    data = _loads_strict_json(raw)

    # validate/normalize
    days = data.get("days")
    if not isinstance(days, list) or len(days) != 7:
        raise ValueError("model did not return 7 days")
    for d in days:
        if not isinstance(d.get("meals"), list) or not d["meals"]:
            raise ValueError("a day is missing meals")
        for m in d["meals"]:
            m["name"] = str(m.get("name", "Meal"))
            m["recipe_text"] = str(m.get("recipe_text", ""))
            for k in ("calories", "protein_g", "carbs_g", "fat_g"):
                v = m.get(k, 0)
                try:
                    m[k] = float(v)
                except Exception:
                    m[k] = 0.0
    return data

# ---------- Local fallback generator (always 7 days) ----------

def _fallback_mealplan(prefs: Dict[str, Any]) -> Dict[str, Any]:
    meals_per_day = int(prefs.get("meals_per_day") or 3)
    excludes = {str(x).lower() for x in prefs.get("exclude_ingredients", [])}

    catalog = [
        ("Greek Yogurt Parfait",   380, 28, 45, 10, "Layer yogurt, berries, granola. Drizzle honey."),
        ("Chicken Quinoa Bowl",    620, 45, 60, 18, "Grilled chicken + quinoa + veg. Lemon/olive oil."),
        ("Salmon Sheet Pan",       560, 38, 35, 24, "Roast salmon & veg; salt/pepper/garlic."),
        ("Tofu Stir Fry",          520, 32, 55, 16, "Tofu + mixed veg + rice + soy/ginger."),
        ("Omelet & Toast",         420, 28, 32, 20, "3-egg omelet, spinach, cheese, whole-grain toast."),
        ("Turkey Wrap",            480, 34, 42, 16, "Whole-wheat wrap, turkey, veg, yogurt sauce."),
        ("Bean Chili",             540, 28, 68, 14, "Kidney/black beans, tomatoes, chili spices."),
        ("Shrimp Pasta",           600, 36, 70, 16, "Shrimp, garlic, olive oil, parsley, pasta."),
        ("Steak & Potatoes",       650, 45, 45, 24, "Pan-seared steak, roasted potatoes, salad."),
    ]
    def ok(name: str) -> bool:
        s = name.lower()
        if "yogurt" in s and ("dairy" in excludes): return False
        if "omelet" in s and ("eggs" in excludes): return False
        if "shrimp" in s and ("shellfish" in excludes): return False
        if "salmon" in s and ("fish" in excludes): return False
        if "wrap"   in s and ("gluten" in excludes): return False
        return True

    pool = [m for m in catalog if ok(m[0])] or catalog
    random.seed(42)

    days: List[Dict[str, Any]] = []
    for d in range(1, 8):
        picks = [pool[(d * i) % len(pool)] for i in range(1, meals_per_day + 1)]
        meals = [{"name": n, "calories": c, "protein_g": p, "carbs_g": cb, "fat_g": f, "recipe_text": r}
                 for (n, c, p, cb, f, r) in picks]
        days.append({"day": d, "meals": meals})

    return {"days": days}

# -------------------- routes --------------------

@bp.get("/preferences")
def get_preferences():
    try:
        claims = _claims_from_auth_header()
        user_id = _oid(claims.get("sub", ""))
        doc = db.user_prefs.find_one({"user_id": user_id}) or {}
        prefs = {
            "calorie_target": doc.get("calorie_target"),
            "protein_g_target": doc.get("protein_g_target"),
            "carb_g_target": doc.get("carb_g_target"),
            "fat_g_target": doc.get("fat_g_target"),
            "diet": doc.get("diet", "balanced"),
            "exclude_ingredients": doc.get("exclude_ingredients", []),
            "cuisine_preferences": doc.get("cuisine_preferences", []),
            "meals_per_day": doc.get("meals_per_day", 3),
            "budget": doc.get("budget", "medium"),
            "max_prep_minutes": doc.get("max_prep_minutes", 30),
        }
        return jsonify({"ok": True, "preferences": prefs})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": f"failed to load preferences: {e}"}), 500

@bp.put("/preferences")
def put_preferences():
    try:
        claims = _claims_from_auth_header()
        user_id = _oid(claims.get("sub", ""))
        body = request.get_json(force=True, silent=True) or {}
        update: Dict[str, Any] = {}

        def copy_num(src, key):
            if key in src and src[key] is not None:
                try:
                    if key.endswith("_g") or "target" in key:
                        update[key] = float(src[key])
                    else:
                        update[key] = int(src[key])
                except Exception:
                    pass

        for k in ["calorie_target", "protein_g_target", "carb_g_target", "fat_g_target",
                  "meals_per_day", "max_prep_minutes"]:
            copy_num(body, k)

        if "diet" in body and isinstance(body["diet"], str):
            update["diet"] = body["diet"]

        if "exclude_ingredients" in body:
            v = body["exclude_ingredients"]
            if isinstance(v, list):
                update["exclude_ingredients"] = [str(x) for x in v if x]

        if "cuisine_preferences" in body:
            v = body["cuisine_preferences"]
            if isinstance(v, list):
                update["cuisine_preferences"] = [str(x) for x in v if x]

        if "budget" in body and isinstance(body["budget"], str):
            update["budget"] = body["budget"]

        if not update:
            return jsonify({"ok": False, "msg": "no valid fields to update"}), 400

        db.user_prefs.update_one(
            {"user_id": user_id},
            {"$set": update, "$setOnInsert": {"user_id": user_id}},
            upsert=True,
        )

        doc = db.user_prefs.find_one({"user_id": user_id}) or {}
        prefs = {
            "calorie_target": doc.get("calorie_target"),
            "protein_g_target": doc.get("protein_g_target"),
            "carb_g_target": doc.get("carb_g_target"),
            "fat_g_target": doc.get("fat_g_target"),
            "diet": doc.get("diet", "balanced"),
            "exclude_ingredients": doc.get("exclude_ingredients", []),
            "cuisine_preferences": doc.get("cuisine_preferences", []),
            "meals_per_day": doc.get("meals_per_day", 3),
            "budget": doc.get("budget", "medium"),
            "max_prep_minutes": doc.get("max_prep_minutes", 30),
        }
        return jsonify({"ok": True, "preferences": prefs})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": f"failed to save preferences: {e}"}), 500

@bp.get("/mealplans")
def get_mealplan():
    try:
        claims = _claims_from_auth_header()
        user_id = _oid(claims.get("sub", ""))
        doc = db.user_prefs.find_one({"user_id": user_id})

        if not doc or "meal_plan" not in doc:
            return jsonify({"ok": True, "mealplan": None})

        return jsonify({"ok": True, "mealplan": doc["meal_plan"]})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": f"failed to load mealplan: {e}"}), 500

@bp.post("/mealplans/save")
def save_mealplan():
    try:
        claims = _claims_from_auth_header()
        user_id = _oid(claims.get("sub", ""))
        body = request.get_json(force=True, silent=True) or {}
        mealplan = body.get("mealplan")

        if not mealplan:
            return jsonify({"ok": False, "msg": "mealplan required"}), 400

        db.user_prefs.update_one(
            {"user_id": user_id},
            {"$set": {"meal_plan": mealplan}, "$setOnInsert": {"user_id": user_id}},
            upsert=True,
        )

        return jsonify({"ok": True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": f"failed to save mealplan: {e}"}), 500

@bp.post("/mealplans/generate")
def generate_mealplan():
    try:
        claims = _claims_from_auth_header()
        user_id = _oid(claims.get("sub", ""))
        prefs = db.user_prefs.find_one({"user_id": user_id}) or {}

        mealplan = None
        if os.getenv("USE_STRANDS", "1") not in ("0", "false", "False"):
            try:
                mealplan = _call_strands_mealplan(prefs)
            except Exception as strands_err:
                print("Strands generation failed:", strands_err)  # visible in Flask console

        if mealplan is None:
            mealplan = _fallback_mealplan(prefs)

        # Save the generated meal plan
        db.user_prefs.update_one(
            {"user_id": user_id},
            {"$set": {"meal_plan": mealplan}, "$setOnInsert": {"user_id": user_id}},
            upsert=True,
        )

        return jsonify({
            "ok": True,
            "prefs_used": {
                "calorie_target": prefs.get("calorie_target"),
                "diet": prefs.get("diet", "balanced"),
                "exclude_ingredients": prefs.get("exclude_ingredients", []),
                "meals_per_day": prefs.get("meals_per_day", 3),
            },
            "mealplan": mealplan,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": f"failed to generate mealplan: {e}"}), 500
