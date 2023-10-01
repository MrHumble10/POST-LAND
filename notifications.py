import os
from smtplib import SMTP

MY_EMAIL = os.environ.get("MY_EMAIL")

EMAIL_PASS = os.environ.get("EMAIL_PASS")




def reply_email(email, name):
    with SMTP("smtp.gmail.com") as connection:

        connection.starttls()
        connection.login(user=MY_EMAIL, password=EMAIL_PASS)
        connection.sendmail(from_addr=MY_EMAIL,
                            to_addrs=email,
                            msg=f"Subject:Reply From POST LAND\n\n"
                                f"Dear {name}\n\n"
                                f"We have just received your Message."
                                f" We will response as soon as possible"
                            )

        print(connection)


def send_email(user_name, user_email, tel, msg):
    with SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(user=MY_EMAIL, password=EMAIL_PASS)
        connection.sendmail(from_addr=user_email,
                            to_addrs=MY_EMAIL,
                            msg=f"Subject:New contact from POST LAND\n\n"
                                f"Name: {user_name}\n\n"
                                f"Email: {user_email}\n\n"
                                f"Phone: {tel}\n\n"
                                f"Message:\n\n"
                                f"{msg}"
                            )
        reply_email(user_email, user_name)
