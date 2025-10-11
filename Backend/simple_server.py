"""
Simple Flask server that mimics the behavior of the actual agent.py
but without requiring the Strands library.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/plan", methods=["POST"])
def plan_meals():
    # Parse JSON body
    data = request.get_json()
    
    if data is None:
        return jsonify({"error": "Invalid or missing JSON data"}), 400
        
    # Here we're just echoing back the request data instead of using Strands
    # This helps test if the client can successfully connect and send data
    return jsonify({
        "status": "ok", 
        "received_data": data,
        "message": "This is a test response. The actual meal planner is not running."
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)