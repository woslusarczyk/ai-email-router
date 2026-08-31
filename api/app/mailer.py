import smtplib
from email.message import EmailMessage

from app.config import SMTP_HOST, SMTP_PORT

SENDER_ADDRESS = "ai-email-router@example.com"


def send_email(to: str, reply_to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = SENDER_ADDRESS
    message["To"] = to
    message["Reply-To"] = reply_to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.send_message(message)
