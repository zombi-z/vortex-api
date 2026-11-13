from flask import request
import smtplib
from email.mime.text import MIMEText
import os

# Add this endpoint for the Sellix/Stripe webhook
@app.route('/webhook/purchase', methods=['POST'])
def purchase_webhook():
    data = request.json
    
    # This is the secret password Sellix will send so we know it's real
    if data.get('secret') != "VORTEX_WEBHOOK_SECRET":
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get the buyer's email and the product they bought from the webhook payload
    # (Note: You will need to adjust these keys to match Sellix's actual JSON payload)
    buyer_email = data.get('customer_email')
    product_name = data.get('product_title', 'Vortex')
    
    # Determine how many days the key should be based on the product name
    days = 1
    if "Week" in product_name:
        days = 7
    elif "Month" in product_name:
        days = 30
    elif "Lifetime" in product_name:
        days = 36500 # 100 years
    
    # Generate the key using our existing function
    new_key = generate_key_string()
    expires_at = datetime.now() + timedelta(days=days)
    
    DATABASE[new_key] = {
        "expires": expires_at.isoformat(),
        "hwid": None 
    }
    
    # --- SEND THE EMAIL ---
    # (You need a Gmail account with an App Password for this to work)
    SENDER_EMAIL = "your_email@gmail.com"
    SENDER_PASSWORD = "your_16_letter_app_password"
    
    msg = MIMEText(f"Thank you for purchasing Vortex!\n\nYour License Key: {new_key}\nExpires: {expires_at.strftime('%Y-%m-%d')}\n\nDownload the loader from your dashboard and paste this key.")
    msg['Subject'] = "Your Vortex License Key"
    msg['From'] = SENDER_EMAIL
    msg['To'] = buyer_email
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"[+] Emailed key {new_key} to {buyer_email}")
    except Exception as e:
        print(f"[!] Failed to email key: {e}")
    
    return jsonify({"success": True, "key": new_key})
