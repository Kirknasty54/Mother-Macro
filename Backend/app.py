from flask import Flask, request, jsonify
from backend_common.envdb import db, ensure_user_indexes
from backend_common.security import verify_password, hash_password
from datetime import datetime, timezone
import re
from strands import Agent

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
    
    # Validate required fields
    required_fields = ["name", "age", "height_cm", "weight_kg", "activity_level", "dietary_restrictions", "dislikes", "goal"]
    for field in required_fields:
        if field not in data:
            return jsonify({"ok": False, "msg": f"Missing required field: {field}"}), 400
    
    # Validate data types and values
    try:
        name = str(data["name"]).strip()
        age = int(data["age"])
        height_cm = float(data["height_cm"])
        weight_kg = float(data["weight_kg"])
        activity_level = str(data["activity_level"]).strip().lower()
        dietary_restrictions = data["dietary_restrictions"] if isinstance(data["dietary_restrictions"], list) else []
        dislikes = data["dislikes"] if isinstance(data["dislikes"], list) else []
        goal = str(data["goal"]).strip().lower()
        
        # Validate ranges and values
        if not name:
            return jsonify({"ok": False, "msg": "Name cannot be empty"}), 400
        if not (1 <= age <= 120):
            return jsonify({"ok": False, "msg": "Age must be between 1 and 120"}), 400
        if not (50 <= height_cm <= 300):
            return jsonify({"ok": False, "msg": "Height must be between 50 and 300 cm"}), 400
        if not (20 <= weight_kg <= 500):
            return jsonify({"ok": False, "msg": "Weight must be between 20 and 500 kg"}), 400
        if activity_level not in ["light", "moderate", "heavy", "very heavy"]:
            return jsonify({"ok": False, "msg": "Activity level must be one of: light, moderate, heavy, very heavy"}), 400
        if goal not in ["maintain", "lose", "gain"]:
            return jsonify({"ok": False, "msg": "Goal must be one of: maintain, lose, gain"}), 400
            
    except (ValueError, TypeError):
        return jsonify({"ok": False, "msg": "Invalid data types in request"}), 400
    
    # Create personalized prompt for the agent
    restrictions_text = ", ".join(dietary_restrictions) if dietary_restrictions else "none"
    dislikes_text = ", ".join(dislikes) if dislikes else "none"
    
    prompt = f"""Create a personalized meal plan for a week for {name} with the following details:
    - Age: {age} years old
    - Height: {height_cm} cm
    - Weight: {weight_kg} kg
    - Activity level: {activity_level}
    - Dietary restrictions: {restrictions_text}
    - Food dislikes: {dislikes_text}
    - Goal: {goal} weight
    
    Please provide a detailed 7-day meal plan with breakfast, lunch, dinner, and snacks that meets their nutritional needs and preferences.
    
    Format your response as a JSON object with the following structure:
    {{
        "daily_plans": [
            {{
                "day": 1,
                "day_name": "Monday",
                "meals": {{
                    "breakfast": {{
                        "name": "meal name",
                        "ingredients": ["ingredient1", "ingredient2"],
                        "calories": 400,
                        "prep_time": "15 minutes",
                        "instructions": "cooking instructions"
                    }},
                    "lunch": {{ ... }},
                    "dinner": {{ ... }},
                    "snacks": [{{ ... }}]
                }},
                "total_calories": 2000,
                "macros": {{
                    "protein_g": 120,
                    "carbs_g": 200,
                    "fat_g": 80,
                    "fiber_g": 25
                }}
            }}
        ],
        "shopping_list": ["item1", "item2", "item3"],
        "nutritional_summary": {{
            "daily_calorie_target": 2000,
            "weekly_average_calories": 2000,
            "protein_percentage": 25,
            "carbs_percentage": 45,
            "fat_percentage": 30
        }}
    }}
    
    Only return the JSON object, no additional text."""
    
    try:
        agent = Agent()
        raw_response = agent(prompt)
        
        # Try to parse the agent's response as JSON
        try:
            import json
            # Clean the response to extract JSON if wrapped in markdown or other text
            response_text = raw_response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            meal_plan_data = json.loads(response_text.strip())
            
            return jsonify({
                "ok": True, 
                "meal_plan": meal_plan_data,
                "user_info": {
                    "name": name,
                    "age": age,
                    "height_cm": height_cm,
                    "weight_kg": weight_kg,
                    "activity_level": activity_level,
                    "goal": goal,
                    "dietary_restrictions": dietary_restrictions,
                    "dislikes": dislikes
                }
            })
            
        except json.JSONDecodeError:
            # Fallback: return raw response if JSON parsing fails
            return jsonify({
                "ok": True, 
                "meal_plan": {
                    "raw_response": raw_response,
                    "note": "Agent response could not be parsed as structured JSON"
                },
                "user_info": {
                    "name": name,
                    "age": age,
                    "height_cm": height_cm,
                    "weight_kg": weight_kg,
                    "activity_level": activity_level,
                    "goal": goal,
                    "dietary_restrictions": dietary_restrictions,
                    "dislikes": dislikes
                }
            })
        
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Failed to generate meal plan: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
