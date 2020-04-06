import datetime
import json
import logging
import os.path

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
            credentials = json.load(credentials_json)["oanda_{}"
                .format(trading_type)]
    except Exception as e:
        logging.exception("{}: Could not read {} credentials from "
                          "credentials.json: ".format(loc, trading_type, e))
        raise

    return credentials

def get_base_url(trading_type):
    return "https://api-fx{}.oanda.com".format(
        "trade" if trading_type == "live" else "practice")

def get_accounts(trading_type="practice"):
    # https://developer.oanda.com/rest-live-v20/account-ep/
    loc = "oanda.py:get_accounts"

    try:
        credentials = get_credentials(trading_type)

        url = "{}/v3/accounts".format(get_base_url(trading_type))
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(credentials["api_key"]),
        }

        response = requests.request("GET", url, headers=headers)

        return response
    except Exception as e:
        logging.exception("{}: Could not get {} accounts from the OANDA API: {}"
                          .format(loc, trading_type, e))
        raise

def get_instruments(trading_type="practice"):
    # https://developer.oanda.com/rest-live-v20/account-ep/
    loc = "oanda.py:get_instruments"

    try:
        credentials = get_credentials(trading_type)

        url = "{}/v3/accounts/{}/instruments".format(
            get_base_url(trading_type),
            credentials["account_id"])

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(credentials["api_key"]),
        }

        instruments_response = requests.request("GET", url, headers=headers)
        instruments = json.loads(instruments_response.text.encode("utf8"))
        return instruments
    except Exception as e:
        logging.exception("{}: Could not get {} instruments from the OANDA "
                          "API: {}".format(loc, trading_type, e))
        raise

def get_price_precision(instrument, trading_type="practice"):
    price_precisions = get_price_precisions(trading_type)
    return price_precisions[instrument]

def get_price_precisions(trading_type="practice"):
    price_precisions_file = "price_precisions.json"

    if os.path.isfile(price_precisions_file):
        price_precisions = load_price_precisions(price_precisions_file)
        # Note that there is just 1 list for both trading types,
        # although I do not think they differ
    else:
        price_precisions = save_price_precisions(
            price_precisions_file, trading_type)

    return price_precisions

def save_price_precisions(price_precisions_file, trading_type="practice"):
    instruments = get_instruments(trading_type)

    price_precisions = {instrument["name"]:instrument["displayPrecision"] for
        instrument in instruments["instruments"]}

    with open("price_precisions.json", "w") as price_precisions_json:
        json.dump(price_precisions, price_precisions_json, indent=2,
                  sort_keys=True)

    return price_precisions

def load_price_precisions(price_precisions_file):
    with open(price_precisions_file) as price_precisions_json:
        price_precisions = (json.load(price_precisions_json))
    return price_precisions

def get_filtered_instruments(instrument_filter="EUR", trading_type="practice"):
    loc = "oanda.py:get_filtered_instruments"

    instruments = get_instruments(trading_type)
    filtered_instruments = list(filter(lambda i: instrument_filter in i,
                                   instruments))

    return filtered_instruments

def buy_order(instrument, units, price, trailing_stop_loss_percent,
              take_profit_percent, trading_type="practice",
              **kwargs):
    # https://developer.oanda.com/rest-live-v20/order-ep/
    loc = "oanda.py:buy_order"

    try:
        credentials = get_credentials(trading_type)
        price_decimals = get_price_precision(instrument, trading_type)

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
            "Authorization": "Bearer {}".format(credentials["api_key"]),
            "Accept-Datetime-Format": "RFC3339"
        }

        response = requests.request(
            "POST", url, headers=headers, data=payload_str)
    except Exception as e:
        logging.exception("{}: Could not send the buy order to OANDA: {}"
                          .format(loc, e))
        raise
    else:
        response_text = response.text.encode("utf8")
        response_json = json.loads(response_text)

        return response_json

def sell_order(instrument, trading_type, **kwargs):
    # https://developer.oanda.com/rest-live-v20/position-ep/
    loc = "oanda.py:sell_order"

    try:
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
            "Authorization":"Bearer {}".format(credentials["api_key"]),
            "Accept-Datetime-Format":"RFC3339"}

        response = requests.request("PUT", url, headers=headers, data=payload_str)
    except Exception as e:
        logging.exception("{}: Could not send the sell order to OANDA: {}"
                          .format(loc, e))
        raise
    else:
        response_text = response.text.encode("utf8")
        response_json = json.loads(response_text)

        return response_json

if __name__ == "__main__":
    # Set logging parameters
    logging.basicConfig(level=logging.INFO)
    loc = "oanda.py"

    # Uncomment this bit to write all instruments and their price
    # precision—for the given trading type—to price_precisions.json, or
    # load them from that file if it exists
    # logging.info("{}: {}".format(loc, json.dumps(
    #     get_price_precisions(), indent=2, sort_keys=True)))

    # Uncomment this bit to send a buy order to OANDA
    order_response = buy_order(
        instrument="XAU_EUR",
        units=1, # i.e. 1 unit (bar?) of gold
        price=1486.891,
        trailing_stop_loss_percent=0.03, # as positive decimal
        take_profit_percent=0.06, # as positive decimal
        trading_type="practice"
    )

    logging.info("{}: {}".format(
        loc, json.dumps(order_response, indent=2, sort_keys=True)))
