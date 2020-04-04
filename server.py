from copy import copy
import itertools
import json
from json.decoder import JSONDecodeError
import logging

import web

import oanda

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

class webhook:
    def POST(self):
        loc = "server.py:webhook:POST"

        # Load the received JSON
        try:
            post_data = json.loads(web.data())
        except JSONDecodeError as e:
            logging.exception("{}: Request received with invalid JSON: {}"
                              .format(loc, e))
            raise web.internalerror("Your JSON could not be read. Please try "
                                    "again.")
        logging.info("{}: Request received with JSON: {}".format(
            loc, json.dumps(post_data, indent=2, sort_keys=True)))

        # And, if it could be loaded, translate it to OANDA parameters
        try:
            oanda_parameters = post_data_to_oanda_parameters(copy(post_data))
        except Exception as e:
            logging.exception("{}: Could not translate received JSON to OANDA "
                              "parameters: {}".format(loc, e))
            raise web.internalerror("Your JSON could be read:\n{}\nbut not "
                                   "translated to OANDA parameters. Please try "
                                   "again.".format(
                json.dumps(post_data, indent=2, sort_keys=True)))
        logging.info("{}: Translated that to: {}".format(
            loc, json.dumps(oanda_parameters, indent=2, sort_keys=True)))

        # Then send those to OANDA as either a buy or sell order
        try:
            if post_data["action"] == "buy":
                order_response = oanda.buy_order(**oanda_parameters)
            elif post_data["action"] == "sell":
                order_response = oanda.sell_order(**oanda_parameters)
            else:
                raise ValueError("You did not specify whether you want to buy "
                                 "or sell")
        except Exception as e:
            logging.exception("{}: Could not send the order to OANDA "
                              "because of an error: {}".format(loc, e))
            raise web.internalerror("Your JSON was read:\n{}\nand translated:"
                                    "\n{}\nbut could not be sent to OANDA. "
                                    "Please try again.".format(
                json.dumps(post_data, indent=2, sort_keys=True),
                json.dumps(oanda_parameters, indent=2, sort_keys=True)))
        logging.info("{}: Sent order to OANDA. This was their response: {}"
                     .format(
            loc, json.dumps(order_response, indent=2, sort_keys=True)))

        # And reply to the POST request
        web.header("Content-Type", "text/plain")
        return ("You sent me this JSON:\n{}\nI translated that to these OANDA "
                "parameters:\n{}\nWhen I sent those to OANDA, they responded "
                "with this:\n{}".format(
            json.dumps(post_data, indent=2, sort_keys=True),
            json.dumps(oanda_parameters, indent=2, sort_keys=True),
            json.dumps(order_response, indent=2, sort_keys=True)
        ))

# Set logging parameters
logging.basicConfig(level=logging.INFO)
loc = "oanda.py"

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
