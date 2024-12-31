from flask import current_app
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import asyncio
import aiosmtplib
import requests
import html
import re


def sanitize_input(input_text):
    return html.escape(input_text.strip())


def validate_email(email):
    pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(pattern, email) is not None


async def verify_recaptcha(recaptcha_response):
    secret = current_app.config['RECAPTCHA_SECRET_KEY']
    payload = {'secret': secret, 'response': recaptcha_response}
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
    result = response.json()
    return result.get("success", False)


async def send_email_async(message, recepient_email):
    email_username = current_app.config['EMAIL_USERNAME']
    if not recepient_email:
        recepient_email = email_username
    message["From"] = email_username
    message["To"] = recepient_email

    try:
        await aiosmtplib.send(
            message,
            hostname=current_app.config['EMAIL_HOST'],
            port=current_app.config['EMAIL_PORT'],
            start_tls=True,
            username=email_username,
            password=current_app.config['EMAIL_PASSWORD'])
        return True
    except Exception as error:
        print(f"Error sending email to {recepient_email}: {str(error)}")
        return False


async def send_text(message: str) -> dict:
    try:
        client = Client(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN']
        )

        response = client.messages.create(
            body=message,
            from_=current_app.config['TWILIO_PHONE_NUMBER'],
            to=current_app.config['RECIPIENT_PHONE_NUMBER']
        )
        print(f"Message sent successfully. Status: {response.status}")
        return {
            'success': True,
            'status': response.status,
            'sid': response.sid
        }

    except TwilioRestException as e:
        print(f"Failed to send message: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'code': e.code
        }


def text_unsent(msg):
    msg['Subject'] = f"An error occurred while sending a text message"
    asyncio.run(send_email_async(message=msg, recepient_email=None))
    print('Text sending error, notified')
