from configparser import ConfigParser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import requests
import time

config = ConfigParser()
config.read('settings.cfg')

# BirdEye API endpoint
API_URL = "https://public-api.birdeye.so/defi/"

# BirdEye API key
API_KEY = config.get('birdeye', 'api')

# Telegram configuration
TELEGRAM_BOT_TOKEN = config['telegram']['bot_token']
TELEGRAM_CHAT_ID = config['telegram']['chat_id']

# Email configuration
SMTP_SERVER = config['email']['smtp_server']
SMTP_PORT = config['email']['smtp_port']
EMAIL_FROM = config['email']['email_from']
EMAIL_TO = config['email']['email_to']
EMAIL_APP_PASSWORD = config['email']['email_app_password']

# Token addresses
TOKENS = {name: address for name, address in config['tokens'].items()}

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, EMAIL_TO, text)
        server.quit()
        print("Email alert sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("Telegram alert sent successfully")
    except requests.RequestException as e:
        print(f"Error sending Telegram message: {e}")

def get_token_price(token_address):
    try:
        headers = {
            'X-API-KEY': API_KEY
        }
        response = requests.get(f"{API_URL}price?address={token_address}", headers=headers)
        response.raise_for_status()
        data = response.json()
        token_value = data['data']['value']
        return token_value
    except requests.RequestException as e:
        print(f"Error fetching price for token {token_address}: {e}")
        return None

def main():
    while True:
        for token_name, token_address in TOKENS.items():
            price = get_token_price(token_address)
            if price is not None:
                message = f"The current price of {token_name} ({token_address}) is: {price}"
                print(message)
                send_telegram_message(message)
        # Wait for 1 minute
        time.sleep(60)

if __name__ == "__main__":
    main()