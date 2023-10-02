from __future__ import print_function
import os
from smtplib import SMTP
import base64
from email.message import EmailMessage

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

MY_EMAIL = os.environ.get("MY_EMAIL")

EMAIL_PASS = os.environ.get("EMAIL_PASS")




# def reply_email(email, name):
#     with SMTP("smtp.gmail.com") as connection:
#
#         connection.starttls()
#         connection.login(user=MY_EMAIL, password=EMAIL_PASS)
#         connection.sendmail(from_addr=MY_EMAIL,
#                             to_addrs=email,
#                             msg=f"Subject:Reply From POST LAND\n\n"
#                                 f"Dear {name}\n\n"
#                                 f"We have just received your Message."
#                                 f" We will response as soon as possible"
#                             )
#
#         print(connection)
#
#
# def send_email(user_name, user_email, tel, msg):
#     with SMTP("smtp.gmail.com", port=443) as connection:
#         connection.starttls()
#         connection.login(user=MY_EMAIL, password=EMAIL_PASS, initial_response_ok=True)
#         connection.sendmail(from_addr=user_email,
#                             to_addrs=MY_EMAIL,
#                             msg=f"Subject:New contact from POST LAND\n\n"
#                                 f"Name: {user_name}\n\n"
#                                 f"Email: {user_email}\n\n"
#                                 f"Phone: {tel}\n\n"
#                                 f"Message:\n\n"
#                                 f"{msg}"
#                             )
#         reply_email(user_email, user_name)
#
#
#
#
#
#

def send_email(user_name, user_email, tel, msg):
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds, _ = google.auth.default()

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message.set_content(
            f'Name: {user_name}\n\n'
            f'Email: {user_email}\n\n'
            f'Phone: {tel}\n\n'
            f'Message:\n\n'
            f'{msg}')

        message['To'] = f'{MY_EMAIL}'
        message['From'] = f'{MY_EMAIL}'
        message['Subject'] = 'NEW POSTLAND MESSAGE'

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
            .decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message
