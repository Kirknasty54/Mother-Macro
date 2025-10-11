import requests
import argparse
import json
import sys

def get_user_input():
    """Interactively collect user data"""
    print("=== Interactive Meal Plan API Test ===\n")
    
    data = {}
    
    # Name
    data["name"] = input("Enter name (default: John): ").strip() or "John"
    
    # Age
    while True:
        try:
            age_input = input("Enter age (default: 30): ").strip()
            data["age"] = int(age_input) if age_input else 30
            break
        except ValueError:
            print("Please enter a valid number for age.")
    
    # Height
    while True:
        try:
            height_input = input("Enter height in cm (default: 180): ").strip()
            data["height_cm"] = int(height_input) if height_input else 180
            break
        except ValueError:
            print("Please enter a valid number for height.")
    
    # Weight
    while True:
        try:
            weight_input = input("Enter weight in kg (default: 75): ").strip()
            data["weight_kg"] = int(weight_input) if weight_input else 75
            break
        except ValueError:
            print("Please enter a valid number for weight.")
    
    # Activity Level
    activity_levels = ["sedentary", "light", "moderate", "active", "very_active"]
    print(f"\nActivity levels: {', '.join(activity_levels)}")
    while True:
        activity = input("Enter activity level (default: moderate): ").strip() or "moderate"
        if activity in activity_levels:
            data["activity_level"] = activity
            break
        else:
            print(f"Please choose from: {', '.join(activity_levels)}")
    
    # Dietary Restrictions
    print("\nEnter dietary restrictions (press Enter when done, or just Enter to skip):")
    restrictions = []
    while True:
        restriction = input("  - Restriction: ").strip()
        if not restriction:
            break
        restrictions.append(restriction)
    data["dietary_restrictions"] = restrictions
    
    # Dislikes
    print("\nEnter foods you dislike (press Enter when done, or just Enter to skip):")
    dislikes = []
    while True:
        dislike = input("  - Dislike: ").strip()
        if not dislike:
            break
        dislikes.append(dislike)
    data["dislikes"] = dislikes
    
    # Caloric Goal
    while True:
        try:
            calorie_input = input("Enter caloric goal (default: 2000): ").strip()
            data["caloric_goal"] = int(calorie_input) if calorie_input else 2000
            break
        except ValueError:
            print("Please enter a valid number for calories.")
    
    # Goal
    goals = ["lose", "maintain", "gain"]
    print(f"\nGoals: {', '.join(goals)}")
    while True:
        goal = input("Enter goal (default: maintain): ").strip() or "maintain"
        if goal in goals:
            data["goal"] = goal
            break
        else:
            print(f"Please choose from: {', '.join(goals)}")
    
    return data

def send_request(data, url="http://127.0.0.1:8000/plan"):
    """Send the request to the API"""
    headers = {"Content-Type": "application/json"}
    
    print(f"\n=== Sending Request to {url} ===")
    print("Data being sent:")
    print(json.dumps(data, indent=2))
    print()
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        # Debugging output
        print("Status Code:", response.status_code)
        print("Response Headers:", dict(response.headers))
        print("Response Text:", response.text)
        print()
        
        # Handle JSON response
        if response.headers.get("Content-Type") == "application/json":
            print("=== JSON Response ===")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Non-JSON response received.")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the server. Make sure it's running on the specified URL.")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Interactive API test tool")
    parser.add_argument("--url", default="http://127.0.0.1:8000/plan", 
                       help="API endpoint URL (default: http://127.0.0.1:8000/plan)")
    parser.add_argument("--preset", choices=["default", "weight_loss", "muscle_gain"], 
                       help="Use a preset configuration")
    parser.add_argument("--json", help="Load data from a JSON file")
    
    args = parser.parse_args()
    
    if args.json:
        try:
            with open(args.json, 'r') as f:
                data = json.load(f)
            print(f"Loaded data from {args.json}")
        except FileNotFoundError:
            print(f"ERROR: File {args.json} not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in {args.json}")
            sys.exit(1)
    elif args.preset == "weight_loss":
        data = {
            "name": "Alice",
            "age": 28,
            "height_cm": 165,
            "weight_kg": 70,
            "activity_level": "active",
            "dietary_restrictions": [],
            "dislikes": ["Brussels sprouts"],
            "caloric_goal": 1500,
            "goal": "lose"
        }
        print("Using weight loss preset")
    elif args.preset == "muscle_gain":
        data = {
            "name": "Mike",
            "age": 25,
            "height_cm": 185,
            "weight_kg": 80,
            "activity_level": "very_active",
            "dietary_restrictions": [],
            "dislikes": [],
            "caloric_goal": 2800,
            "goal": "gain"
        }
        print("Using muscle gain preset")
    elif args.preset == "default":
        data = {
            "name": "John",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 75,
            "activity_level": "moderate",
            "dietary_restrictions": [],
            "dislikes": [],
            "caloric_goal": 2000,
            "goal": "maintain"
        }
        print("Using default preset")
    else:
        # Interactive mode
        data = get_user_input()
    
    send_request(data, args.url)

if __name__ == "__main__":
    main()