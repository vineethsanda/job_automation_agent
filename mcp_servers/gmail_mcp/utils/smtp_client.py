"""SMTP client wrapper for Gmail email sending."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

class SMTPClientWrapper:
    """High-level SMTP wrapper for Gmail."""

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465

    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password

    def send_reply(
        self,
        to_address: str,
        subject: str,
        body: str,
        original_message_id: Optional[str] = None,
        cc: Optional[list[str]] = None,
    ) -> bool:
        """Send a reply email."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
            msg["From"] = self.email_address
            msg["To"] = to_address

            if cc:
                msg["Cc"] = ", ".join(cc)

            if original_message_id:
                msg["In-Reply-To"] = original_message_id
                msg["References"] = original_message_id

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.login(self.email_address, self.app_password)
                server.send_message(msg)

            logger.info(f"Reply sent to {to_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            return False

    def send_application_email(
        self,
        to_address: str,
        applicant_name: str,
        position: str,
        company: str,
        body: str,
    ) -> bool:
        """Send a job application follow-up email."""
        subject = f"Job Application: {position} at {company}"

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_address
            msg["To"] = to_address

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.login(self.email_address, self.app_password)
                server.send_message(msg)

            logger.info(f"Application email sent to {to_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to send application email: {e}")
            return False
