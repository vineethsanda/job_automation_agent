"""IMAP client for Gmail operations."""

import imaplib
import email
import re
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
load_dotenv()


class GmailIMAPClient:
    """IMAP client for Gmail mailbox operations."""

    IMAP_SERVER = "imap.gmail.com"
    POLL_INTERVAL = 30  # seconds

    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password
        self.imap: Optional[imaplib.IMAP4_SSL] = None
        self._connect()

    def _connect(self) -> None:
        """Establish IMAP connection to Gmail."""
        try:
            self.imap = imaplib.IMAP4_SSL(self.IMAP_SERVER, 993)
            self.imap.login(self.email_address, self.app_password)
            logger.info(f"Connected to Gmail IMAP as {self.email_address}")
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            raise

    def fetch_unread(self, mailbox: str = "INBOX", max_results: int = 10) -> List[Dict]:
        """Fetch unread emails from specified mailbox."""
        try:
            self.imap.select(mailbox)
            _, message_numbers = self.imap.search(None, "UNSEEN")
            
            emails = []
            for msg_num in message_numbers[0].split()[-max_results:]:
                _, data = self.imap.fetch(msg_num, "(RFC822)")
                email_data = email.message_from_bytes(data[0][1])

                emails.append({
                    "msg_id": msg_num.decode(),
                    "from": email_data.get("From", ""),
                    "subject": email_data.get("Subject", ""),
                    "date": email_data.get("Date", ""),
                    "body": self._extract_body(email_data),
                    "timestamp": datetime.utcnow().isoformat(),
                })

            logger.info(f"Fetched {len(emails)} unread emails from {mailbox}")
            return emails
        except Exception as e:
            logger.error(f"Failed to fetch unread emails: {e}")
            return []

    def read_thread(self, subject: str, max_messages: int = 7) -> List[Dict]:
        """Read email thread by subject, limit to last N messages."""
        try:
            self.imap.select("INBOX")
            _, message_numbers = self.imap.search(None, f'SUBJECT "{subject}"')

            thread = []
            # Get last max_messages emails in thread
            for msg_num in message_numbers[0].split()[-max_messages:]:
                _, data = self.imap.fetch(msg_num, "(RFC822)")
                email_data = email.message_from_bytes(data[0][1])

                thread.append({
                    "from": email_data.get("From", ""),
                    "subject": email_data.get("Subject", ""),
                    "date": email_data.get("Date", ""),
                    "body": self._extract_body(email_data),
                })

            logger.debug(f"Read thread with {len(thread)} messages: {subject}")
            return thread
        except Exception as e:
            logger.error(f"Failed to read thread: {e}")
            return []

    def extract_otp(
        self,
        sender_filter: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> Optional[str]:
        """Extract OTP from recent emails within timeout window."""
        start_time = datetime.utcnow()

        while (datetime.utcnow() - start_time).seconds <= timeout_seconds:
            try:
                self.imap.select("INBOX")
                _, message_numbers = self.imap.search(None, "UNSEEN")

                for msg_num in message_numbers[0].split()[-5:]:
                    _, data = self.imap.fetch(msg_num, "(RFC822)")
                    email_data = email.message_from_bytes(data[0][1])

                    # Filter by sender if specified
                    if sender_filter and sender_filter not in email_data.get("From", ""):
                        continue

                    body = self._extract_body(email_data)
                    otp = self._extract_code_from_text(body)

                    if otp:
                        logger.info(f"Extracted OTP: {otp}")
                        return otp

                logger.debug("No OTP found, waiting...")
                time.sleep(5)

            except Exception as e:
                logger.error(f"Error extracting OTP: {e}")
                time.sleep(5)

        logger.warning(f"OTP not found within {timeout_seconds}s")
        return None

    @staticmethod
    def _extract_body(email_data: email.message.Message) -> str:
        """Extract text body from email message."""
        body = ""
        if email_data.is_multipart():
            for part in email_data.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = email_data.get_payload(decode=True).decode("utf-8", errors="ignore")
        return body

    @staticmethod
    def _extract_code_from_text(text: str) -> Optional[str]:
        """Extract 6-digit code or alphanumeric code from text."""
        # Look for 6-digit code
        match = re.search(r"\b(\d{6})\b", text)
        if match:
            return match.group(1)

        # Look for OTP label patterns
        for pattern in [
            r"(?:OTP|code|verification)[:\s]+([A-Z0-9]{6,})",
            r"(?:OTP|code|verification)[:\s]+(\d{6,})",
        ]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def mark_as_read(self, msg_id: str, mailbox: str = "INBOX") -> bool:
        """Mark an email as read by message ID."""
        try:
            self.imap.select(mailbox)
            # msg_id could be the message number (bytes) from IMAP search
            _, _ = self.imap.store(msg_id, "+FLAGS", "\\Seen")
            logger.debug(f"Marked email {msg_id} as read")
            return True
        except Exception as e:
            logger.error(f"Failed to mark email {msg_id} as read: {e}")
            return False

    def close(self) -> None:
        """Close IMAP connection."""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
                logger.info("IMAP connection closed")
            except Exception as e:
                logger.error(f"Error closing IMAP: {e}")


class GmailSMTPClient:
    """SMTP client for sending emails via Gmail."""

    SMTP_SERVER = "smtp.gmail.com"

    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password

    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        reply_to: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> bool:
        """Send email via SMTP."""
        try:
            import smtplib

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_address
            msg["To"] = to_address

            if reply_to:
                msg["Reply-To"] = reply_to
            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to
                msg["References"] = in_reply_to

            # Add plain text and HTML versions
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL(self.SMTP_SERVER, 465) as server:
                server.login(self.email_address, self.app_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_address}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
