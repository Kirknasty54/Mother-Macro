from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from flask import Flask, request, jsonify

# Load environment variables from .env file
load_dotenv()

# Configure OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found in environment variables")

# Strands imports
from strands import Agent
from strands.multiagent.swarm import Swarm, SharedContext

# --- Pydantic schema for incoming form ---
class PreferenceForm(BaseModel):
    name: str
    age: int
    height_cm: int
    weight_kg: float
    activity_level: str  # sedentary, light, moderate, active, very_active
    dietary_restrictions: List[str] = []  # e.g. ["vegetarian", "gluten-free"]
    dislikes: List[str] = []
    caloric_goal: int = None  # optional - will be calculated if not provided
    goal: str  # "lose", "maintain", "gain"

app = Flask(__name__)

# --- Placeholder nutrition tool ---
# In production, replace with a real tool that queries a nutrition DB or API.
def nutrition_lookup_tool(query: str) -> Dict[str, Any]:
    # Very small mock database
    db = {
        "chicken breast": {"cal": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6},
        "brown rice (1 cup)": {"cal": 216, "protein_g": 5, "carbs_g": 44, "fat_g": 1.8},
        "broccoli (1 cup)": {"cal": 55, "protein_g": 3.7, "carbs_g": 11.2, "fat_g": 0.6},
        "oats (1 cup)": {"cal": 307, "protein_g": 11, "carbs_g": 55, "fat_g": 5.3},
    }
    return db.get(query.lower(), {"cal": 100, "protein_g": 5, "carbs_g": 10, "fat_g": 3})

# --- Agent factory functions ---
# Each agent is a thin wrapper around an LLM-driven Agent with a role prompt.

def create_intake_agent():
    prompt = (
        "You are Intake Agent. Validate the user's form and compute a suggested daily calorie target. "
        "Return JSON with keys: validated_form, suggested_calories."
    )
    return Agent(name="IntakeAgent", system_prompt=prompt)


def create_nutrition_agent():
    prompt = (
        "You are Nutrition Agent. Given a list of ingredients or dishes, return macronutrients and calories. "
        "You can call a local nutrition_lookup_tool for exact numbers."
    )
    # pass the tool as a Python-callable that the agent can call
    return Agent(name="NutritionAgent", system_prompt=prompt, tools=[nutrition_lookup_tool])


def create_planner_agent():
    prompt = (
        "You are Planner Agent. Using the validated form and nutrition info, create a 7-day meal plan (3 meals + 1 snack per day) that meets the daily calorie target and respects restrictions. "
        "Return JSON with: meal_plan (dict day->meals), shopping_list (list), daily_totals (cal/protein/carbs/fat)."
    )
    return Agent(name="PlannerAgent", system_prompt=prompt)

# --- Core orchestration using Strands Swarm ---
async def run_meal_planner_swarm(form: PreferenceForm) -> Dict[str, Any]:
    # create agents
    intake = create_intake_agent()
    nutrition = create_nutrition_agent()
    planner = create_planner_agent()

    # build swarm: pass agents list directly (no shared_context parameter)
    swarm = Swarm([intake, nutrition, planner])

    # prepare form data for the swarm
    # Use model_dump() for Pydantic v2, or dict() for v1
    try:
        # For Pydantic v2
        form_data = form.model_dump()
    except AttributeError:
        # Fallback for Pydantic v1
        form_data = form.dict()

    # Give a top-level goal for the swarm with the form data included
    goal = (
        f"Produce a 7-day meal plan and corresponding shopping list for the user with the following preferences: {form_data}. "
        "First validate and enrich the user data, then look up nutrition information as needed, "
        "and finally create a complete meal plan that meets their caloric goals and dietary restrictions."
    )

    # Run the swarm using the correct API
    result = await swarm.invoke_async(goal)
    
    # Extract the result content
    if hasattr(result, 'content') and result.content:
        return result.content
    elif hasattr(result, 'response'):
        return result.response
    else:
        return str(result)


# --- Flask endpoint ---
@app.route("/plan", methods=["POST"])
def plan_meals():
    # Parse JSON body
    data = request.get_json()
    form = PreferenceForm(**data)
    # Create meal plan using simple agent
    plan = create_meal_plan(form)
    return jsonify({"status": "ok", "plan": plan})


# --- Standalone runner for local testing ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
