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
1. Connect the local web.py server with the OANDA API call
1. Test if a request from Postman to the web.py server running locally reaches OANDA correctly
1. Move the server to PythonAnywhere so that TradingView can reach it
1. Setup TradingView to send an alert to the server on PythonAnywhere
1. Test if an alert from TradingView reaches OANDA correctly

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
