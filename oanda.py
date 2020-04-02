import datetime
import json
import logging
import requests

logging.basicConfig(level=logging.INFO)

def get_datetime_offset(offset_minutes=15):
    # In RFC3339
    now = datetime.datetime.utcnow()
    now_plus_offset = now + datetime.timedelta(minutes=offset_minutes)
    return "{}Z".format(now_plus_offset.isoformat("T"))

def get_datetime_now():
    now = datetime.datetime.utcnow()
    return "{}Z".format(now.isoformat("T"))

def get_credentials(trading_type):
    try:
        with open("credentials.json") as credentials_json:
            credentials = (json.load(credentials_json))
    except:
        logging.exception("oanda.py/load_credentials: Could not read "
                          "credentials from credentials.json")
        return False

    if not "{}_credentials".format(trading_type) in credentials:
        logging.exception("oanda.py/load_credentials: Could not find "
                          "'{}_credentials' in credentials.json".format(
            trading_type))
        return False

    return credentials["{}_credentials".format(trading_type)]

def get_base_url(trading_type):
    return "https://api-fx{}.oanda.com".format(
        "trade" if trading_type == "live" else "practice")

def get_accounts(trading_type="practice"):
    # https://developer.oanda.com/rest-live-v20/account-ep/

    credentials = get_credentials(trading_type)

    url = "{}/v3/accounts".format(get_base_url(trading_type))
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(credentials["oanda_key"]),
    }

    response = requests.request("GET", url, headers=headers)
    logging.info("oanda.py/get_accounts: {}".format(response.text.encode("utf8")))

def get_instruments(trading_type="practice"):
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

    logging.info("oanda.py/get_instruments: {}".format(instruments_list))

    return instruments_list

def get_filtered_instruments(instrument_filter="EUR", trading_type="practice"):
    instruments = get_instruments(trading_type)
    filtered_instruments = list(filter(lambda i: instrument_filter in i,
                                   instruments))

    logging.info("oanda.py/get_filtered_instruments({}): {}".format(
        instrument_filter,
        filtered_instruments))

    return filtered_instruments

def post_order(instrument, units, price, stop_loss_percent,
               trailing_stop_loss_percent, take_profit_percent,
               price_decimals=3,
               trading_type="practice"):
    # https://developer.oanda.com/rest-live-v20/order-ep/

    credentials = get_credentials(trading_type)

    url = "{}/v3/accounts/{}/orders".format(
        get_base_url(trading_type),
        credentials["account_id"]
    )

    # Convert the entered percentages to the absolute values OANDA expects
    stop_loss_price = price * (1 - stop_loss_percent)
    trailing_stop_loss_distance = trailing_stop_loss_percent * price
    take_profit_price = price * (1 + take_profit_percent)

    payload = {
        "order": {
            "type": "LIMIT",
            "positionFill": "DEFAULT",
            "timeInForce": "GTD",
            "gtdTime": get_datetime_offset(15),
            "instrument": instrument,
            "units": "{}".format(units),
            "price": "{0:.{1}f}".format(price, price_decimals),
            "stopLossOnFill": {
                "timeInForce": "GTC",
                "price": "{0:.{1}f}".format(stop_loss_price, price_decimals),
                "clientExtensions":{
                    "comment": "oanda.py/post_order/stop_loss",
                    "tag": "stop_loss",
                    "id": "{}_stop_loss".format(get_datetime_now())
                },
            },
            "trailingStopLossOnFill": {
                "distance": "{0:.{1}f}".format(trailing_stop_loss_distance, price_decimals),
                "timeInForce": "GTC",
                "clientExtensions": {
                    "comment": "oanda.py/post_order/trailing_stop_loss",
                    "tag": "trailing_stop_loss",
                    "id": "{}_trailing_stop_loss".format(get_datetime_now())
                },
            },
            "takeProfitOnFill": {
                "price": "{0:.{1}f}".format(take_profit_price, price_decimals),
                "clientExtensions": {
                    "comment": "oanda.py/post_order/take_profit",
                    "tag": "take_profit",
                    "id": "{}_take_profit".format(get_datetime_now())
                },
            },
            "clientExtensions": {
                "comment": "oanda.py/post_order/entry",
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
    logging.info(response_text)



if __name__ == "__main__":
    post_order(
        instrument="XAU_EUR",
        units=1000,
        price=1490.322,
        stop_loss_percent=0.03, # as positive decimal
        trailing_stop_loss_percent=0.01, # as positive decimal
        take_profit_percent=0.06, # as positive decimal
        trading_type="practice"
    )
