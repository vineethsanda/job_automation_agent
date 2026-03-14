"""Gmail MCP Server - Email management via Model Context Protocol."""

import os
from typing import Optional
from mcp.server.fastmcp import FastMCP
from loguru import logger

from utils.imap_client import GmailIMAPClient, GmailSMTPClient
from utils.smtp_client import SMTPClientWrapper
from tools.fetch_unread import fetch_unread_emails
from tools.send_reply import send_reply
from tools.read_thread import read_thread
from tools.extract_otp import extract_otp


# Initialize FastMCP server
mcp = FastMCP("gmail_mcp")

# Global clients (initialized at startup)
imap_client: Optional[GmailIMAPClient] = None
smtp_client: Optional[SMTPClientWrapper] = None


@mcp.tool()
async def fetch_unread(
    mailbox: str = "INBOX",
    max_results: int = 10,
) -> dict:
    """
    Fetch unread emails from Gmail.

    Args:
        mailbox: Mailbox name (INBOX, Sent, etc.)
        max_results: Maximum number of emails to return

    Returns:
        Dictionary containing unread emails and metadata
    """
    if not imap_client:
        return {"status": "error", "error": "IMAP client not initialized"}

    return await fetch_unread_emails(imap_client, mailbox, max_results)


@mcp.tool()
async def send_email_reply(
    to_address: str,
    subject: str,
    body: str,
    original_message_id: Optional[str] = None,
    cc: Optional[list[str]] = None,
) -> dict:
    """
    Send an email reply.

    Args:
        to_address: Recipient email address
        subject: Email subject
        body: Email body text
        original_message_id: Original message ID for threading
        cc: List of CC recipients

    Returns:
        Dictionary with send status
    """
    if not smtp_client:
        return {"status": "error", "error": "SMTP client not initialized"}

    return await send_reply(
        smtp_client, to_address, subject, body, original_message_id, cc
    )


@mcp.tool()
async def read_email_thread(
    subject: str,
    max_messages: int = 7,
) -> dict:
    """
    Read an email thread by subject.

    Args:
        subject: Email subject to search for
        max_messages: Maximum messages to retrieve

    Returns:
        Dictionary with thread messages
    """
    if not imap_client:
        return {"status": "error", "error": "IMAP client not initialized"}

    return await read_thread(imap_client, subject, max_messages)


@mcp.tool()
async def get_otp_code(
    sender_filter: Optional[str] = None,
    timeout_seconds: int = 120,
) -> dict:
    """
    Extract OTP code from recent emails.

    Args:
        sender_filter: Optional email sender to filter
        timeout_seconds: Timeout for OTP extraction

    Returns:
        Dictionary with OTP code or timeout status
    """
    if not imap_client:
        return {"status": "error", "error": "IMAP client not initialized"}

    return await extract_otp(imap_client, sender_filter, timeout_seconds)


def initialize_clients() -> bool:
    """Initialize IMAP and SMTP clients from environment variables."""
    global imap_client, smtp_client

    try:
        email_address = os.getenv("GMAIL_ADDRESS")
        app_password = os.getenv("GMAIL_APP_PASSWORD")

        if not email_address or not app_password:
            logger.error("Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD env vars")
            return False

        imap_client = GmailIMAPClient(email_address, app_password)
        smtp_client = SMTPClientWrapper(email_address, app_password)

        logger.info(f"Gmail clients initialized for {email_address}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Gmail clients: {e}")
        return False


@mcp.on_startup
async def on_startup() -> None:
    """Initialize server on startup."""
    logger.info("Gmail MCP Server starting...")
    if not initialize_clients():
        logger.error("Failed to initialize Gmail clients")


@mcp.on_shutdown
async def on_shutdown() -> None:
    """Cleanup on shutdown."""
    global imap_client
    if imap_client:
        imap_client.close()
        logger.info("IMAP connection closed")


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        "logs/gmail_mcp.log",
        rotation="10 MB",
        retention=3,
        level="DEBUG",
    )

    # Run server
    logger.info("Starting Gmail MCP Server...")
    mcp.run()
