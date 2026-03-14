"""Tool for sending email replies via Gmail."""

from typing import Optional, Dict
from loguru import logger
from dotenv import load_dotenv
load_dotenv()


async def send_reply(
    smtp_client,
    to_address: str,
    subject: str,
    body: str,
    original_message_id: Optional[str] = None,
    cc: Optional[list[str]] = None,
) -> Dict:
    """
    Send an email reply.

    Args:
        smtp_client: SMTPClientWrapper instance
        to_address: Recipient email address
        subject: Email subject
        body: Email body text
        original_message_id: Original message ID for threading
        cc: CC recipients list

    Returns:
        Dictionary with status and result
    """
    try:
        success = smtp_client.send_reply(
            to_address=to_address,
            subject=subject,
            body=body,
            original_message_id=original_message_id,
            cc=cc,
        )

        return {
            "status": "success" if success else "failed",
            "to_address": to_address,
            "subject": subject,
        }
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")
        return {
            "status": "error",
            "error": str(e),
            "to_address": to_address,
        }
