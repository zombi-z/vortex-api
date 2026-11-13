from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)

# Temporary database (resets on server restart)
DATABASE = {} 
ADMIN_PASSWORD = "VORTEX_ADMIN_123"

def generate_key_string():
    return "VORTEX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

# 1. ENDPOINT: Generate key (Used by your Discord Bot)
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

# 2. ENDPOINT: Verify key (Used by your Loader)
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

# 3. ENDPOINT: Sellix Webhook (Auto-delivery)
@app.route('/webhook/purchase', methods=['POST'])
def purchase_webhook():
    data = request.json
    
    # Only process paid orders
    if data.get('event') != 'order.paid':
        return jsonify({"success": True, "message": "Ignored"}), 200

    order_data = data.get('data', {})
    
    # Extract email and price
    buyer_email = order_data.get('customer', {}).get('email', 'unknown@email.com')
    amount = order_data.get('amount', 100) # Price in cents
    
    # Determine duration based on price
    if amount == 100:
        days = 1
    elif amount == 500:
        days = 7
    elif amount == 1000:
        days = 30
    elif amount >= 3000:
        days = 36500 # Lifetime
    else:
        days = 1 # Default fallback
        
    # Generate Key
    new_key = generate_key_string()
    expires_at = datetime.now() + timedelta(days=days)
    
    DATABASE[new_key] = {
        "expires": expires_at.isoformat(),
        "hwid": None 
    }
    
    print(f"\n==========================================")
    print(f"[+] NEW SALE RECEIVED!")
    print(f"[+] Email: {buyer_email}")
    print(f"[+] Price: {amount / 100}")
    print(f"[+] Generated Key: {new_key}")
    print(f"==========================================\n")
    
    return jsonify({"success": True, "key": new_key})

if __name__ == '__main__':
    print("Vortex API is running...")
    app.run(port=5000)
