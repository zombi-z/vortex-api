from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)

# This is our temporary database (it resets when the server restarts)
DATABASE = {} 
ADMIN_PASSWORD = "VORTEX_ADMIN_123"

# Helper function to generate a random key
def generate_key_string():
    return "VORTEX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

# 1. ENDPOINT: Generate a new key (Admin Only)
@app.route('/generate', methods=['POST'])
def generate_key():
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 403
    
    days = int(data.get('days', 1)) 
    new_key = generate_key_string()
    
    expires_at = datetime.now() + timedelta(days=days)
    
    DATABASE[new_key] = {
        "expires": expires_at.isoformat(),
        "hwid": None 
    }
    
    return jsonify({
        "success": True, 
        "key": new_key, 
        "expires": expires_at.strftime("%Y-%m-%d %H:%M:%S")
    })

# 2. ENDPOINT: Verify a key (Used by your Loader)
@app.route('/verify', methods=['POST'])
def verify_key():
    data = request.json
    user_key = data.get('key')
    user_hwid = data.get('hwid')
    
    if not user_key or not user_hwid:
        return jsonify({"error": "Missing key or HWID"}), 400
        
    if user_key not in DATABASE:
        return jsonify({"error": "Invalid key"}), 404
        
    key_data = DATABASE[user_key]
    
    expires_at = datetime.fromisoformat(key_data["expires"])
    if datetime.now() > expires_at:
        return jsonify({"error": "Key expired"}), 403
        
    if key_data["hwid"] is None:
        key_data["hwid"] = user_hwid
        return jsonify({"success": True, "message": "Key activated and bound to your PC!"})
    elif key_data["hwid"] != user_hwid:
        return jsonify({"error": "Key is locked to another PC"}), 403
        
    return jsonify({"success": True, "message": "Welcome back!"})

if __name__ == '__main__':
    print("Vortex API is running on port 5000...")
    app.run(port=5000)