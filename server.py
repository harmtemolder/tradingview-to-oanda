from copy import copy
import itertools
import json
from json.decoder import JSONDecodeError
import logging

import web

from oanda import buy_order, sell_order, get_datetime_now
from sendgrid_api import send_mail

def fill_defaults(post_data):
    loc = "server.py:fill_defaults"
    try:
        instrument = post_data["instrument"]
        price = float(post_data["price"])
    except KeyError as e:
        logging.exception("{}: One of the required parameters was missing: {}"
                          .format(loc, e))
        raise

    units = (
        int(post_data["units"])
        if "units" in post_data
        else 500) # e.g. in Euros for "EURUSD" or in gold for "XAUEUR"
    trailing_stop_loss_percent = (
        float(post_data["trailing_stop_loss_percent"])
        if "trailing_stop_loss_percent" in post_data
        else 0.01) # as positive decimal
    take_profit_percent = (
        float(post_data["take_profit_percent"])
        if "take_profit_percent" in post_data
        else 0.06) # as positive decimal
    trading_type = (
        post_data["trading_type"]
        if "trading_type" in post_data
        else "practice")

    return {
        "instrument": instrument,
        "units": units,
        "price": price,
        "trailing_stop_loss_percent": trailing_stop_loss_percent,
        "take_profit_percent": take_profit_percent,
        "trading_type": trading_type,
    }

def translate(post_data):
    loc = "server.py:translate"

    try:
        # Translate `ticker` to `instrument` by adding a "_"
        ticker = post_data.pop("ticker")
        if len(ticker) == 6:
            post_data["instrument"] = "{}_{}".format(ticker[:3], ticker[3:])
        else:
            raise ValueError("This ticker does not match my assumptions")

    except KeyError as e:
        logging.exception("{}: One of the parameters I am trying to translate "
                          "does not exist: {}".format(loc, e))
        raise
    except ValueError as e:
        logging.exception("{}: One of the parameters I am trying to translate "
                          "does not match my assumptions: {}".format(loc, e))
        raise

    return post_data

def post_data_to_oanda_parameters(post_data):
    loc = "server.py:post_data_to_oanda_parameters"

    try:
        translated_data = translate(post_data)
        filled_data = fill_defaults(translated_data)
    except Exception as e:
        logging.exception("{}: Could not translate data or fill all"
                          "defaults: {}".format(loc, e))
        raise

    return filled_data

class log:
    def __init__(self):
        self.content = ""

    def __str__(self):
        return str(self.content)

    def add(self, message):
        if len(self.content) > 0:
            self.content += "\n"

        self.content = "{}{}: {}".format(
            self.content, get_datetime_now(), message)

class webhook:
    def POST(self):
        loc = "server.py:webhook:POST"
        local_log = log()

        web_data = web.data()

        # Load the received JSON
        try:
            post_data = json.loads(web_data)
        except JSONDecodeError as e:
            error_message = ("{}: Request received with invalid JSON: {}".format(loc, e))
            logging.exception(error_message)

            local_log.add("ERROR:root:{}:\n{}".format(
                error_message, web_data))

            mail_response = send_mail(
                "TradingView to OANDA: Fail", str(local_log))
            local_log.add("INFO:ROOT:{}: I also sent you this log through "
                          "SendGrid. They replied with status code {}: {}"
                .format(loc, mail_response.status_code, mail_response.body))

            raise web.internalerror(local_log)

        info_message = "{}: Request received with valid JSON".format(loc)
        logging.info(info_message)
        local_log.add("INFO:ROOT:{}:\n{}".format(
                info_message, json.dumps(post_data, indent=2, sort_keys=True)))

        # And, if it could be loaded, translate it to OANDA parameters
        try:
            oanda_parameters = post_data_to_oanda_parameters(copy(post_data))
        except Exception as e:
            error_message = ("{}: Could not translate JSON to OANDA "
                             "parameters: {}".format(loc, e))
            logging.exception(error_message)

            local_log.add("ERROR:root:{}".format(error_message))

            mail_response = send_mail(
                "TradingView to OANDA: Fail", str(local_log))
            local_log.add("INFO:ROOT:{}: I also sent you this log through "
                          "SendGrid. They replied with status code {}: {}"
                .format(loc, mail_response.status_code, mail_response.body))

            raise web.internalerror(local_log)
        info_message = ("{}: Translated that to OANDA parameters".format(loc))
        logging.info(info_message)
        local_log.add("INFO:ROOT:{}:\n{}".format(
            info_message, json.dumps(
                oanda_parameters, indent=2, sort_keys=True)))

        # Then send those to OANDA as either a buy or sell order
        try:
            if post_data["action"] == "buy":
                order_response = buy_order(**oanda_parameters)
                mail_subject = ("TradingView to OANDA: Sent an order to buy {} "
                                "units of {}".format(
                    oanda_parameters["units"], oanda_parameters["instrument"]))
            elif post_data["action"] == "sell":
                order_response = sell_order(**oanda_parameters)
                mail_subject = ("TradingView to OANDA: Sent an order to close "
                                "all positions of {}".format(
                    oanda_parameters["instrument"]))
            else:
                raise ValueError("You did not specify whether you want to buy "
                                 "or sell")
        except Exception as e:
            error_message = ("{}: Could not send the order to OANDA because of "
                             "an error: {}".format(loc, e))
            logging.exception(error_message)

            local_log.add("ERROR:root:{}".format(error_message))

            mail_response = send_mail(
                "TradingView to OANDA: Fail", str(local_log))
            local_log.add("INFO:ROOT:{}: I also sent you this log through "
                          "SendGrid. They replied with status code {}: {}"
                .format(loc, mail_response.status_code, mail_response.body))

            raise web.internalerror(local_log)
        info_message = "{}: Sent order to OANDA".format(loc)
        logging.info(info_message)
        local_log.add("INFO:ROOT:{}:\n{}".format(info_message,
            json.dumps(order_response, indent=2, sort_keys=True)))

        # Mail the log and reply to the POST request
        mail_response = send_mail(mail_subject, str(local_log))
        local_log.add("INFO:ROOT:{}: I also sent you this log through "
                      "SendGrid. They replied with status code {}: {}".format(
            loc, mail_response.status_code, mail_response.body))

        web.header("Content-Type", "text/plain")
        return (local_log)

# Set logging parameters
logging.basicConfig(level=logging.INFO)
loc = "server.py"

# Load the list of access tokens and set webhook URLs for each one
try:
    with open("access_tokens.json") as access_tokens_json:
        access_tokens = (json.load(access_tokens_json))
except JSONDecodeError as e:
    logging.exception(
        "{}: Could not read tokens from access_tokens.json: {}".format(loc, e))
    raise

urls = tuple(itertools.chain.from_iterable(
    ["/webhook/{}".format(token)] + ["webhook"] for token in access_tokens))

# Set up the server
app = web.application(urls, globals())

if __name__ == "__main__":
    # Start the server
    logging.info("{}: Starting the server".format(loc))
    app.run()
