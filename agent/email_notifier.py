
import smtplib
from email.message import EmailMessage
from .config import Settings

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def send_email(settings: Settings, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.gmail_address
    message["To"] = settings.alert_to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP_SSL(
        SMTP_HOST,
        SMTP_PORT,
        local_hostname="localhost",
        timeout=30
    ) as smtp:
        smtp.login(settings.gmail_address, settings.gmail_app_password)
        smtp.send_message(message)


def send_test_email(settings: Settings) -> None:
    send_email(
        settings,
        "NVIDIA Job Hunter – בדיקת חיבור",
        "שלום!\n\n"
        "זוהי הודעת בדיקה מ-NVIDIA Job Hunter.\n"
        "אם קיבלת את ההודעה, חיבור Gmail באמצעות SMTP הצליח.\n"
    )
