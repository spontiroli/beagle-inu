from configparser import ConfigParser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import requests
import time
import json

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

# Token addresses and alert conditions from config
TOKENS = {name: json.loads(config['tokens'][name]) for name in config['tokens']}

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
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print(message)
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

def should_alert(price, condition, target_price):
    if condition == 'greater_than' and price > target_price:
        return True
    if condition == 'less_than' and price < target_price:
        return True
    # TODO trim decimal digits (if not it will never match)
    if condition == 'equal' and price == target_price:
        return True
    return False

def main():
    while True:
        for token_name, token_info in TOKENS.items():
            token_address = token_info['address']
            price = get_token_price(token_address)
            if price is not None:

                # TODO only print if debug enabled
                # TODO dockerize
                # TODO add docstrings for methods
                # BUG when alerting once and saving back configuration file

                print(f"The current price of {token_name.upper()} is: {price}")
                for condition_info in token_info['conditions']:
                    if condition_info.get('enabled', True):
                        condition = condition_info['condition']
                        target_price = condition_info['price']
                        
                        if should_alert(price, condition, target_price):
                            message = f"\N{POLICE CARS REVOLVING LIGHT} *Alert*: The price of {token_name.upper()} is {condition.replace('_', ' ')} {target_price}: *{price}*"
                            send_telegram_message(message)
                            # TODO review email alert
                            # send_email(f"Price Alert: {token_name}", message)    

                            # Disable the condition (alert once)
                            condition_info['enabled'] = False
                            config['tokens'][token_name] = json.dumps(token_info, indent=4)
                            with open('settings.cfg', 'w') as configfile:
                                config.write(configfile)
        # Wait a bit
        time.sleep(5)

if __name__ == "__main__":
    main()