# TradingView to OANDA

## Summary
I'm setting up a web.py server that can run on PythonAnywhere (uploaded there through GitHub) which listens to TradingView alerts on a URL (i.e. webhook) and posts orders (and sets stop-losses, etc.) on OANDA through their API

## To-do
1. Set up the web.py server
1. Have it listen to POST requests (test with Postman)
1. Parse the parameters sent in the request to variables that can be sent along to OANDA
1. Authenticate with the OANDA API
1. Send a test order to OANDA's paper trader
1. Add stop-losses and other risk management techniques to the OANDA call
1. Test if a request from Postman reaches OANDA correctly
1. Move the server to PythonAnywhere so that TradingView can reach it
1. Setup TradingView to send an alert to the server on PythonAnywhere
1. Test if an alert from TradingView reaches OANDA correctly
