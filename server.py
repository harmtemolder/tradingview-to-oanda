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
        size = float(post_data["size"])
        price = float(post_data["price"])
    except KeyError:
        logging.exception("{}: One of the required parameters was missing"
                          .format(loc))
    else:
        trailing_stop_loss_percent = (
            float(post_data["trailing_stop_loss_percent"])
            if "trailing_stop_loss_percent" in post_data
            else 0.01) # as positive decimal
        take_profit_percent = (
            float(post_data["take_profit_percent"])
            if "take_profit_percent" in post_data
            else 0.06) # as positive decimal
        price_decimals = (
            post_data["price_decimals"]
            if "price_decimals" in post_data
            else 3) # the number of decimals of precision
        trading_type = (
            post_data["trading_type"]
            if "trading_type" in post_data
            else "practice")

        return {
            "instrument": instrument,
            "size": size,
            "price": price,
            "trailing_stop_loss_percent": trailing_stop_loss_percent,
            "take_profit_percent": take_profit_percent,
            "price_decimals": price_decimals,
            "trading_type": trading_type,
        }

def post_data_to_oanda_parameters(post_data):
    loc = "server.py:post_data_to_oanda_parameters"

    filled_data = fill_defaults(post_data)
    return filled_data

class webhook:
    def POST(self):
        loc = "server.py:webhook:POST"

        # Load the received JSON
        try:
            post_data = json.loads(web.data())
        except JSONDecodeError:
            logging.exception("{}: Request received with invalid JSON"
                              .format(loc))
            raise web.internalerror("Your JSON could not be read. Please try "
                                    "again.")
        else:
            logging.info("{}: Request received with JSON: {}".format(
                loc, json.dumps(post_data, indent=2, sort_keys=True)))

            # And, if it could be loaded, send it to OANDA
            oanda_parameters = post_data_to_oanda_parameters(post_data)
            order_response = oanda.post_order(**oanda_parameters)

            logging.info("{}: Sent order to OANDA.".format(loc))

            web.header("Content-Type", "text/plain")
            return "Thanks for POSTing a valid JSON. Goodbye."

# Set logging parameters
logging.basicConfig(level=logging.INFO)
loc = "oanda.py"

# Load the list of access tokens and set webhook URLs for each one
try:
    with open("access_tokens.json") as access_tokens_json:
        access_tokens = (json.load(access_tokens_json))
except:
    logging.exception(
        "{}: Could not read tokens from access_tokens.json".format(loc))

urls = tuple(itertools.chain.from_iterable(
    ["/webhook/{}".format(token)] + ["webhook"] for token in access_tokens))

# Set up the server
app = web.application(urls, globals())

if __name__ == "__main__":
    # Start the server
    app.run()
