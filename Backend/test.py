import requests

url = "http://127.0.0.1:5000/createPlan"
headers = {"Content-Type": "application/json"}
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

response = requests.post(url, json=data, headers=headers)

# Debugging output
print("Status Code:", response.status_code)
print("Response Headers:", response.headers)
print("Response Text:", response.text)

# Handle JSON response
if response.headers.get("Content-Type") == "application/json":
    print(response.json())
else:
    print("Non-JSON response received.")