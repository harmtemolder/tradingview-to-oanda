import json

import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from oanda import get_datetime_now

def get_credentials():
    loc = "sendgrid_api.py:get_credentials"
    try:
        with open("credentials.json") as credentials_json:
            credentials = (json.load(credentials_json))["sendgrid"]
    except:
        logging.exception("{}: Could not read credentials from credentials.json"
                          .format(loc))
        raise

    return credentials

def send_mail(subject, message):
    # https://github.com/sendgrid/sendgrid-python

    loc = "sendgrid_api.py:send_mail"

    credentials = get_credentials()

    mail_to_send = Mail(
        from_email=credentials["email_address"],
        to_emails=credentials["email_address"],
        subject=subject,
        plain_text_content=message,
        html_content=None)

    try:
        sendgrid_client = SendGridAPIClient(credentials["api_key"])
        response = sendgrid_client.send(mail_to_send)

        return response
    except Exception as e:
        logging.exception("{}: Email could not be sent: {}".format(loc, e))
        raise

def success_mail(message):
    response = send_mail("TradingView to OANDA: Success", message)
    return response

def fail_mail(message):
    response = send_mail("TradingView to OANDA: Fail", message)
    return response

if __name__ == "__main__":
    # Set logging parameters
    logging.basicConfig(level=logging.INFO)
    loc = "sendgrid_api.py"

    response = send_mail(
        subject="SendGrid test from within {}".format(loc),
        message=get_datetime_now()
    )

    logging.info("{}: Email sent successfully. SendGrid answered with a {} "
                 "statuscode: {}".format(
        loc, response.status_code, response.body))