"""Tool for reading email threads."""

from typing import Dict, Optional
from loguru import logger


async def read_thread(
    imap_client,
    subject: str,
    max_messages: int = 7,
) -> Dict:
    """
    Read email thread by subject.

    Args:
        imap_client: GmailIMAPClient instance
        subject: Email subject to search for
        max_messages: Maximum messages to retrieve (default: 7)

    Returns:
        Dictionary with thread messages and metadata
    """
    try:
        thread = imap_client.read_thread(subject, max_messages)
        return {
            "status": "success",
            "subject": subject,
            "message_count": len(thread),
            "messages": thread,
        }
    except Exception as e:
        logger.error(f"Failed to read thread: {e}")
        return {
            "status": "error",
            "error": str(e),
            "subject": subject,
            "messages": [],
        }
