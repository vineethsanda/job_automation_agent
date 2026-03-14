"""Tool for fetching unread emails from Gmail."""

from typing import List, Dict
from loguru import logger


async def fetch_unread_emails(
    imap_client,
    mailbox: str = "INBOX",
    max_results: int = 10,
) -> Dict:
    """
    Fetch unread emails from Gmail.

    Args:
        imap_client: GmailIMAPClient instance
        mailbox: Mailbox name (default: INBOX)
        max_results: Maximum number of results

    Returns:
        Dictionary with email list and metadata
    """
    try:
        emails = imap_client.fetch_unread(mailbox, max_results)
        return {
            "status": "success",
            "count": len(emails),
            "emails": emails,
            "mailbox": mailbox,
        }
    except Exception as e:
        logger.error(f"Failed to fetch unread emails: {e}")
        return {
            "status": "error",
            "error": str(e),
            "count": 0,
            "emails": [],
        }
