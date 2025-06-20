


import requests
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Pull secrets
STRIKE_API_KEY = os.getenv("STRIKE_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENTS = os.getenv("RECIPIENTS").split(",")




# Get BTC price from Strike API
def get_btc_price():
    url = "https://api.strike.me/v1/rates/ticker" # Adjust if needed
    headers = {"Authorization": f"Bearer {STRIKE_API_KEY}"}
    response = requests.get(url, headers=headers)
    data = response.json()

  # Find BTC → USD pair
    for item in data:
        if item["sourceCurrency"] == "BTC" and item["targetCurrency"] == "USD":
            return float(item["amount"])

    raise ValueError("BTC→USD rate not found")

    print("🔍 JSON from Strike:", data)  # <— Add this to inspect
    
    return float(data["rate"])  # Temporary: we’ll fix this next

     


# Email sending function
def send_email(subject, body, to_emails):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ",  ".join(to_emails)
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


price = get_btc_price()
print(f"Live BTC price from Strike API: ${price:,.2f}")

threshold = 100_000





# TEMPORARY: fake price for testing while waiting on API key
# price = 99_950
# print(f"Live BTC price from Strike: ${price:,.2f}")



# threshold = 100_000

# price = get_btc_price()
# print(f"Current BTC price: ${price}")










if price < threshold:
    message = f"BTC dropped below ${threshold:,.2f}. Current price: ${price:,.2f}! Time to stack more sats?"
    print(message)
    send_email("BTC Price Alert", message, RECIPIENTS)
else:
    message = f"BTC is steady at ${price:,.2f}. Probably should still stack more sats!"
    print(message)
    send_email("BTC Update", message, RECIPIENTS)






# from email.message import EmailMessage




# RECIPIENTS = os.getenv("RECIPIENTS").split(",") ## logic to make a list of emails to send to! pulling from the .env secrets
