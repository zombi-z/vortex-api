from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
DATABASE = {} 
ADMIN_PASSWORD = "VORTEX_ADMIN_123"

def generate_key_string():
    return "VORTEX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

@app.route('/generate', methods=['POST'])
def generate_key():
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 403
    
    days = int(data.get('days', 0))
    minutes = int(data.get('minutes', 0))
    
    if days == 0 and minutes == 0:
        days = 1
        
    new_key = generate_key_string()
    expires_at = datetime.now() + timedelta(days=days, minutes=minutes)
    
    DATABASE[new_key] = {
        "expires": expires_at.isoformat(),
        "hwid": None 
    }
    
    return jsonify({
        "success": True, 
        "key": new_key, 
        "expires": expires_at.strftime("%Y-%m-%d %H:%M:%S")
    })

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
        return jsonify({"success": True, "message": "Key activated!"})
    elif key_data["hwid"] != user_hwid:
        return jsonify({"error": "Key is locked to another PC"}), 403
        
    return jsonify({"success": True, "message": "Welcome back!"})

if __name__ == '__main__':
    app.run(port=5000)
