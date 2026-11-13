from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import string
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# Temporary database
DATABASE = {} 
ADMIN_PASSWORD = "VORTEX_ADMIN_123"

# --- EMAIL CONFIGURATION ---
SENDER_EMAIL = "vortex.support.app@gmail.com" # <--- PUT YOUR GMAIL HERE
SENDER_PASSWORD = "ofjqrrhjswdxtaxl"       # <--- PUT YOUR NEW APP PASSWORD HERE (No spaces)

def generate_key_string():
    return "VORTEX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

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

@app.route('/webhook/purchase', methods=['POST'])
def purchase_webhook():
    data = request.json
    
    if data.get('event') != 'order.paid':
        return jsonify({"success": True, "message": "Ignored"}), 200

    order_data = data.get('data', {})
    buyer_email = order_data.get('customer', {}).get('email', 'unknown@email.com')
    amount = order_data.get('amount', 100) 
    
    if amount == 100: days = 1
    elif amount == 500: days = 7
    elif amount == 1000: days = 30
    elif amount >= 3000: days = 36500
    else: days = 1
        
    new_key = generate_key_string()
    expires_at = datetime.now() + timedelta(days=days)
    
    DATABASE[new_key] = {
        "expires": expires_at.isoformat(),
        "hwid": None 
    }
    
    print(f"[+] NEW SALE! Generated {new_key} for {buyer_email}")
    
    # --- SEND EMAIL ---
    if buyer_email != 'unknown@email.com':
        msg = MIMEText(f"Thank you for purchasing Vortex!\n\nYour License Key: {new_key}\nExpires: {expires_at.strftime('%Y-%m-%d')}\n\nDownload the loader and paste this key to inject.")
        msg['Subject'] = "Your Vortex License Key"
        msg['From'] = SENDER_EMAIL
        msg['To'] = buyer_email
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            print(f"[+] Successfully emailed key to {buyer_email}")
        except Exception as e:
            print(f"[!] Failed to email: {e}")
    
    return jsonify({"success": True, "key": new_key})

if __name__ == '__main__':
    print("Vortex API is running...")
    app.run(port=5000)
