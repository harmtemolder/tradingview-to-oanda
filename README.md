# TradingView to OANDA

## Summary
I'm setting up a [web.py](https://webpy.org/) server that can run on PythonAnywhere (uploaded there through GitHub) which listens to TradingView alerts on a URL (i.e. webhook) and posts orders (and sets stop-losses, etc.) on OANDA through their API

## To-do
1. ~~Set up development environment~~
1. ~~Install and set up the web.py server~~
1. ~~Have it listen to POST requests (test with Postman)~~
1. ~~Parse the parameters sent in the request to variables that can be sent along to OANDA~~
1. ~~Authenticate with the OANDA API~~
1. ~~Send a test order to OANDA's paper trader~~
1. ~~Add stop-losses and other risk management techniques to the OANDA call~~
1. ~~Connect the local web.py server with the OANDA API call~~
1. ~~Test if a request from Postman to the web.py server running locally reaches OANDA correctly~~
1. ~~Add some kind of verification so that only I can send orders through my webhook~~
1. Move the server to PythonAnywhere so that TradingView can reach it
1. Setup TradingView to send an alert to the server on PythonAnywhere
1. Test if an alert from TradingView reaches OANDA correctly
1. Add a mechanism that notifies me of every order (email, maybe?)
1. Find out why my limit order didn't go through in the beginning, but cancelled because it reaches the GTD. Maybe the market was closed? If that was the case the market won't move and there won't be any signals, right?

## Prerequisites
* `pip install web.py`
* `conda install requests`
* a `credentials.json` file containing a JSON like this:

```json
{
  "practice_credentials": {
    "oanda_key": "<YOUR PRACTICE ACCOUNT API KEY>",
    "account_id": "<YOUR PRACTICE ACCOUNT ID>"
  },
  "live_credentials": {
    "oanda_key": "<YOUR LIVE ACCOUNT API KEY>",
    "account_id": "<YOUR LIVE ACCOUNT ID>"
  }
}
```

## Authentication
The webhook is only available on `/webhook/<ACCESS_TOKEN>` where `<ACCESS_TOKEN>` is one of the items in the JSON list in `access_tokens.json`. Create that file with the following contents:

```json
[
  "<ACCESS_TOKEN>"
]
```

Make sure to replace `<ACCESS_TOKEN>` with an access token of your choice (e.g. [have DuckDuckGo generate one for you](https://duckduckgo.com/?q=password+64))

Note that these are the only valid endpoints. The server won't tell you anything if you're trying to reach it somewhere else.
