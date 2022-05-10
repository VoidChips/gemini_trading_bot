import os
from dotenv import load_dotenv
import requests
import json
import base64
import hmac
import hashlib
import datetime
import time

TRADING_FEE = 0.004

# get the amount currency 1 can buy currency 2 with at the price of currency 2
def get_trade_amount(trading_with_amount: float, coin_price: float) -> float:
    amount = trading_with_amount / coin_price
    amount = round(amount, 6)  # round to 6 decimal places
    return amount

def get_payload_nonce() -> str:
    t = datetime.datetime.now()
    return str(int(time.mktime(t.timetuple())*100))

# get the available balance of a specific currency
def available_currency_amount(data, currency: str) -> float:
    for currency_data in data:
        if currency_data["currency"] == currency:
            return float(currency_data["available"])

# get the fee adjusted amount of currency
def fee_adjusted(amount: float) -> float:
    return amount * (1 - TRADING_FEE)

load_dotenv()

# get api credentials from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET").encode()

base_url: str = "https://api.gemini.com"
buy_url: str = base_url + "/v1/order/new"

payload_nonce = get_payload_nonce()
payload = {
    "request": "/v1/balances",
    "nonce": payload_nonce
}

encoded_payload = json.dumps(payload).encode()
b64 = base64.b64encode(encoded_payload)
signature = hmac.new(API_SECRET, b64, hashlib.sha384).hexdigest()

request_headers = {'Content-Type': "text/plain",
                        'Content-Length': "0",
                        'X-GEMINI-APIKEY': API_KEY,
                        'X-GEMINI-PAYLOAD': b64,
                        'X-GEMINI-SIGNATURE': signature,
                        'Cache-Control': "no-cache"}


response = requests.post(base_url + "/v1/balances",
                        data=None,
                        headers=request_headers)
data = response.json()
available_balance = available_currency_amount(data, 'GUSD')
print(f"available gusd: {available_balance}")

payload_nonce = get_payload_nonce()

# get eth's price and convert to float
response = requests.get(base_url + "/v1/pubticker/ethgusd")
data = response.json()
price = float(data["last"])
amount = get_trade_amount(fee_adjusted(available_balance), price)

print(f"eth/gusd: {price}")
print(f"{available_balance} gusd to ethgusd: {amount}")

