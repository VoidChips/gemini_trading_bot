import os
from dotenv import load_dotenv
import requests
import json
import base64
import hmac
import hashlib
import datetime
import time

TRADING_FEE: float = 0.004

# get api credentials from environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET").encode()

BASE_URL: str = "https://api.gemini.com"
BALANCE_URL: str = "/v1/balances"
PRICE_URL: str = "/v1/pubticker/"
BUY_URL: str = "/v1/order/new"
ORDER_STATUS_URL: str = "/v1/order/status"

# get the amount currency 1 can buy currency 2 with at the price of currency 2
def get_trade_amount(trading_with_amount: float, coin_price: float) -> float:
    amount = trading_with_amount / coin_price
    amount = round(amount, 6)  # round to 6 decimal places
    return amount

# get increased nonce by waiting 1 second
def get_payload_nonce() -> str:
    time.sleep(1)  # wait 1 second
    t = datetime.datetime.now()
    return str(int(time.mktime(t.timetuple())*100))

# get the available balance of a specific currency
def available_currency_amount(currency: str) -> float:
    try:
        payload = {
            "request": "/v1/balances",
            "nonce": get_payload_nonce()
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


        response = requests.post(BASE_URL + BALANCE_URL,
                                 data=None,
                                 headers=request_headers)
        data = response.json()

        for currency_data in data:
            if currency_data["currency"] == currency:
                return float(currency_data["available"])
        return 0.0
    except:
        print(f"Error getting balance. Gemini may be down.")
        return -1.0

# buy a currency if there is enough balance
def buy_currency(available_balance: float, minimum_balance: float, currency_to_pay: int, currency_to_buy: str) -> str:
    available_balance = fee_adjusted(available_balance)

    if available_balance >= minimum_balance:
        # get eth's price and convert to float
        price = get_currency_price(currency_to_buy)
        amount = get_trade_amount(available_balance, price)

        print(f"{currency_to_buy}: {price}")
        print(f"buying {amount} {currency_to_buy}...")

        payload = {
            "request": BUY_URL,
            "nonce": get_payload_nonce(),
            "symbol": currency_to_buy,
            "amount": str(amount),
            "price": str(price - 1),
            "side": "buy",
            "type": "exchange limit",
            "options": ["maker-or-cancel"]
        }

        encoded_payload = json.dumps(payload).encode()
        b64 = base64.b64encode(encoded_payload)
        signature = hmac.new(API_SECRET, b64,
                                hashlib.sha384).hexdigest()

        request_headers = {'Content-Type': "text/plain",
                                'Content-Length': "0",
                                'X-GEMINI-APIKEY': API_KEY,
                                'X-GEMINI-PAYLOAD': b64,
                                'X-GEMINI-SIGNATURE': signature,
                                'Cache-Control': "no-cache"}

        try:
            response = requests.post(BASE_URL + BUY_URL,
                                    data=None,
                                    headers=request_headers)
            order = response.json()
            # print(order)
            if "order_id" in order:
                return int(order["order_id"])
        except:
            print(f"Error buying {currency_to_buy}. Gemini may be down.")
        return -1

# get the trading fee adjusted amount of currency
def fee_adjusted(amount: float) -> float:
    return amount * (1 - TRADING_FEE)

# get the currency's price
def get_currency_price(currency: str) -> float:
    try:
        response = requests.get(BASE_URL + PRICE_URL + currency)
        data = response.json()
        return float(data["last"])
    except:
        print(f"Error getting price. Gemini may be down.")
        return -1.0

# get the order history
# returns true if order was filled
def get_order_history(order_id: int) -> bool:
    payload = {
        "request": ORDER_STATUS_URL,
        "nonce": get_payload_nonce(),
        "order_id": order_id,
        "include_trades": True
    }

    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(API_SECRET, b64,
                            hashlib.sha384).hexdigest()

    request_headers = {'Content-Type': "text/plain",
                            'Content-Length': "0",
                            'X-GEMINI-APIKEY': API_KEY,
                            'X-GEMINI-PAYLOAD': b64,
                            'X-GEMINI-SIGNATURE': signature,
                            'Cache-Control': "no-cache"}

    try:
        response = requests.post(BASE_URL + ORDER_STATUS_URL,
                                data=None,
                                headers=request_headers)
        status = response.json()
        # request was successful
        if "result" not in status:
            return not status["is_live"]
        # request failed
        else:
            return False
    except:
        print(f"Error checking order status. Order may not exist or Gemini may be down.")
    return False


available_balance = available_currency_amount("GUSD")
print(f"available GUSD: {available_balance}")

# trade if there is at least 10 GUSD available
order_id: int = buy_currency(available_balance, 10.0, "gusd", "ethgusd")
if order_id != -1:
    print(f"waiting for buy order {order_id} to be filled...")

    while not get_order_history(order_id):
        time.sleep(1)  # wait 1 second
        continue
    print(f"order {order_id} was filled or cancelled")

