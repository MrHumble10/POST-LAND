from mailjet_rest import Client
import os


def send_email(user_name, user_email, tel, msg):
    api_key = os.environ.get("MJ_APIKEY_PUBLIC")
    api_secret = os.environ.get("MJ_APIKEY_PRIVATE")
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "humble.py2017@gmail.com",
                    "Name": "Me"
                },
                "To": [
                    {
                        "Email": "humble.py2017@gmail.com",
                        "Name": "You"
                    }
                ],
                "Subject": "NEW POSTLAND MESSAGE!",
                "TextPart": f"User Information!\n\nNAME: {user_name}\n\nEMAIL: {user_email}\n\nTell: {tel}\n\n{msg}",
                "HTMLPart": ""
            }
        ]
    }
    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())
