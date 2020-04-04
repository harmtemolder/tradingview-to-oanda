import datetime
import json
import logging
import math

import requests

def get_datetime_offset(offset_minutes=15):
    # In RFC3339
    now = datetime.datetime.utcnow()
    now_plus_offset = now + datetime.timedelta(minutes=offset_minutes)
    return "{}Z".format(now_plus_offset.isoformat("T"))

def get_datetime_now():
    now = datetime.datetime.utcnow()
    return "{}Z".format(now.isoformat("T"))

def get_credentials(trading_type):
    loc = "oanda.py:get_credentials"
    try:
        with open("credentials.json") as credentials_json:
            credentials = (json.load(credentials_json))
    except:
        logging.exception("{}: Could not read credentials from credentials.json"
                          .format(loc))
        return False

    if not "{}_credentials".format(trading_type) in credentials:
        logging.exception("{}: Could not find '{}_credentials' in credentials"
                          ".json".format(loc, trading_type))
        return False

    return credentials["{}_credentials".format(trading_type)]

def get_base_url(trading_type):
    return "https://api-fx{}.oanda.com".format(
        "trade" if trading_type == "live" else "practice")

def get_accounts(trading_type="practice"):
    loc = "oanda.py:get_accounts"
    # https://developer.oanda.com/rest-live-v20/account-ep/

    credentials = get_credentials(trading_type)

    url = "{}/v3/accounts".format(get_base_url(trading_type))
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(credentials["oanda_key"]),
    }

    response = requests.request("GET", url, headers=headers)
    logging.info("{}: {}".format(loc, response.text.encode("utf8")))

def get_instruments(trading_type="practice"):
    loc = "oanda.py:get_instruments"
    # https://developer.oanda.com/rest-live-v20/account-ep/

    credentials = get_credentials(trading_type)

    url = "{}/v3/accounts/{}/instruments".format(
        get_base_url(trading_type),
        credentials["account_id"])

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(credentials["oanda_key"]),
    }

    response = requests.request("GET", url, headers=headers)

    instruments = json.loads(response.text.encode("utf8"))
    instruments_list = [instrument["name"] for instrument in instruments["instruments"]]

    logging.info("{}: {}".format(loc, instruments_list))

    return instruments_list

def get_filtered_instruments(instrument_filter="EUR", trading_type="practice"):
    loc = "oanda.py:get_filtered_instruments"
    instruments = get_instruments(trading_type)
    filtered_instruments = list(filter(lambda i: instrument_filter in i,
                                   instruments))

    logging.info("{}({}): {}".format(loc, instrument_filter,
                                     filtered_instruments))

    return filtered_instruments

def buy_order(instrument, units, price, trailing_stop_loss_percent,
              take_profit_percent, price_decimals=3, trading_type="practice",
              **kwargs):
    # https://developer.oanda.com/rest-live-v20/order-ep/

    loc = "oanda.py:buy_order"

    credentials = get_credentials(trading_type)

    url = "{}/v3/accounts/{}/orders".format(
        get_base_url(trading_type),
        credentials["account_id"]
    )

    # Convert the entered percentages to the absolute values OANDA expects
    trailing_stop_loss_distance = trailing_stop_loss_percent * price
    take_profit_price = price * (1 + take_profit_percent)

    payload = {
        "order": {
            "type": "LIMIT",
            "positionFill": "DEFAULT",
            "timeInForce": "GTD",
            "gtdTime": get_datetime_offset(15), # i.e. 15 m from now
            "instrument": instrument,
            "units": "{0:d}".format(units), # whole units
            "price": "{0:.{1}f}".format(price, price_decimals),
            "trailingStopLossOnFill": {
                "distance": "{0:.{1}f}".format(trailing_stop_loss_distance,
                                               price_decimals),
                "timeInForce": "GTC",
                "clientExtensions": {
                    "comment": "oanda.py/buy_order/trailing_stop_loss",
                    "tag": "trailing_stop_loss",
                    "id": "{}_trailing_stop_loss".format(get_datetime_now())
                },
            },
            "takeProfitOnFill": {
                "price": "{0:.{1}f}".format(take_profit_price, price_decimals),
                "clientExtensions": {
                    "comment": "oanda.py/buy_order/take_profit",
                    "tag": "take_profit",
                    "id": "{}_take_profit".format(get_datetime_now())
                },
            },
            "clientExtensions": {
                "comment": "oanda.py/buy_order/entry",
                "tag": "entry",
                "id": "{}_entry".format(get_datetime_now())
            },
        }
    }

    payload_str = json.dumps(payload)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(credentials["oanda_key"]),
        "Accept-Datetime-Format": "RFC3339"
    }

    response = requests.request("POST", url, headers=headers, data=payload_str)
    response_text = response.text.encode("utf8")
    response_json = json.loads(response_text)

    logging.info("{}: {}".format(
        loc, json.dumps(response_json, indent=2, sort_keys=True)))

    return response_json

def sell_order(instrument, trading_type, **kwargs):
    # https://developer.oanda.com/rest-live-v20/position-ep/

    loc = "oanda.py:sell_order"

    credentials = get_credentials(trading_type)

    url = "{}/v3/accounts/{}/positions/{}/close".format(
        get_base_url(trading_type),
        credentials["account_id"],
        instrument)

    payload = {
        "longUnits": "ALL",
        "longClientExtensions": {
                "comment": "oanda.py/sell_order/close",
                "tag": "close",
                "id": "{}_close".format(get_datetime_now())
            },
        "shortUnits": "NONE",
    }

    payload_str = json.dumps(payload)
    headers = {
        "Content-Type":"application/json",
        "Authorization":"Bearer {}".format(credentials["oanda_key"]),
        "Accept-Datetime-Format":"RFC3339"}

    response = requests.request("PUT", url, headers=headers, data=payload_str)
    response_text = response.text.encode("utf8")
    response_json = json.loads(response_text)

    logging.info("{}: {}".format(loc,
        json.dumps(response_json, indent=2, sort_keys=True)))

    return response_json


logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    order_response = buy_order(
        instrument="XAU_EUR",
        units=1, # i.e. 1 unit (bar?) of gold
        price=1486.891,
        trailing_stop_loss_percent=0.03, # as positive decimal
        take_profit_percent=0.06, # as positive decimal
        price_decimals=3, # the number of decimals of precision
        trading_type="practice"
    )
