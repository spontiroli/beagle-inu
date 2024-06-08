from configparser import ConfigParser
import requests
import time

config = ConfigParser()
config.read('settings.cfg')

# BirdEye API endpoint
API_URL = "https://public-api.birdeye.so/defi/price?address="

# BirdEye API key
API_KEY = config.get('birdeye', 'api')

# Token addresses
TOKENS = {name: address for name, address in config['tokens'].items()}

def get_token_price(token_address):
    try:
        headers = {
            'X-API-KEY': API_KEY
        }
        response = requests.get(f"{API_URL}{token_address}", headers=headers)
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
                print(f"The current price of {token_name} ({token_address}) is: {price}")
        # Wait for 1 minute
        time.sleep(1)

if __name__ == "__main__":
    main()