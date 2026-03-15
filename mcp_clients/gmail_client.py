"""MCP Client for Gmail server operations."""

import asyncio
import json
from typing import Dict, List, Optional, Any
from loguru import logger

# We'll first try to use the direct IMAP/SMTP clients if MCP server not available
from mcp_servers.gmail_mcp.utils.imap_client import GmailIMAPClient
from mcp_servers.gmail_mcp.utils.smtp_client import SMTPClientWrapper
import os


class GmailMCPClient:
    """Client for Gmail MCP operations (with fallback to direct client)."""

    def __init__(self, email_address: str = None, app_password: str = None):
        """
        Initialize Gmail MCP Client.
        
        Args:
            email_address: Gmail address (uses GMAIL_ADDRESS env var if not provided)
            app_password: Gmail app password (uses GMAIL_APP_PASSWORD env var if not provided)
        """
        self.email_address = email_address or os.getenv("GMAIL_ADDRESS")
        self.app_password = app_password or os.getenv("GMAIL_APP_PASSWORD")
        
        self.imap_client: Optional[GmailIMAPClient] = None
        self.smtp_client: Optional[SMTPClientWrapper] = None
        self.is_connected = False
        
    async def connect(self) -> bool:
        """Connect to Gmail using IMAP and SMTP clients."""
        try:
            if not self.email_address or not self.app_password:
                logger.error("Gmail credentials not provided")
                return False
                
            self.imap_client = GmailIMAPClient(self.email_address, self.app_password)
            self.smtp_client = SMTPClientWrapper(self.email_address, self.app_password)
            
            self.is_connected = True
            logger.info(f"✅ Connected to Gmail: {self.email_address}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Gmail: {e}")
            self.is_connected = False
            return False

    async def fetch_unread_emails(
        self, 
        mailbox: str = "INBOX", 
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Fetch unread emails from Gmail.
        
        Args:
            mailbox: Mailbox name (INBOX, Sent, etc.)
            max_results: Maximum number of emails to return
            
        Returns:
            Dictionary with email list and metadata
        """
        try:
            if not self.is_connected or not self.imap_client:
                logger.error("Gmail client not connected")
                return {
                    "status": "error",
                    "error": "Not connected to Gmail",
                    "emails": [],
                    "count": 0
                }
            
            emails = self.imap_client.fetch_unread(mailbox, max_results)
            
            logger.info(f"✉️  Fetched {len(emails)} unread emails from {mailbox}")
            
            return {
                "status": "success",
                "mailbox": mailbox,
                "count": len(emails),
                "emails": emails
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch unread emails: {e}")
            return {
                "status": "error",
                "error": str(e),
                "emails": [],
                "count": 0
            }

    async def send_email_reply(
        self,
        to_address: str,
        subject: str,
        body: str,
        original_message_id: Optional[str] = None,
        cc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
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
        try:
            if not self.is_connected or not self.smtp_client:
                logger.error("SMTP client not connected")
                return {
                    "status": "error",
                    "error": "Not connected to Gmail SMTP",
                    "to_address": to_address
                }
            
            success = self.smtp_client.send_reply(
                to_address=to_address,
                subject=subject,
                body=body,
                original_message_id=original_message_id,
                cc=cc
            )
            
            if success:
                logger.info(f"📧 Email sent to {to_address} - Subject: {subject}")
                return {
                    "status": "success",
                    "to_address": to_address,
                    "subject": subject
                }
            else:
                logger.error(f"Failed to send email to {to_address}")
                return {
                    "status": "failed",
                    "to_address": to_address,
                    "error": "SMTP send failed"
                }
                
        except Exception as e:
            logger.error(f"Exception while sending email: {e}")
            return {
                "status": "error",
                "error": str(e),
                "to_address": to_address
            }

    async def read_email_thread(
        self,
        subject: str,
        max_messages: int = 7
    ) -> Dict[str, Any]:
        """
        Read an email thread by subject.
        
        Args:
            subject: Email subject to search for
            max_messages: Maximum messages to retrieve
            
        Returns:
            Dictionary with thread messages
        """
        try:
            if not self.is_connected or not self.imap_client:
                logger.error("Gmail client not connected")
                return {
                    "status": "error",
                    "error": "Not connected to Gmail",
                    "messages": []
                }
            
            thread = self.imap_client.read_thread(subject, max_messages)
            
            logger.debug(f"Read thread: {subject} ({len(thread)} messages)")
            
            return {
                "status": "success",
                "subject": subject,
                "count": len(thread),
                "messages": thread
            }
            
        except Exception as e:
            logger.error(f"Failed to read email thread: {e}")
            return {
                "status": "error",
                "error": str(e),
                "messages": []
            }

    async def extract_otp(
        self,
        sender_filter: Optional[str] = None,
        timeout_seconds: int = 120
    ) -> Dict[str, Any]:
        """
        Extract OTP code from recent emails.
        
        Args:
            sender_filter: Optional email sender to filter
            timeout_seconds: Timeout for OTP extraction
            
        Returns:
            Dictionary with OTP code or timeout status
        """
        try:
            if not self.is_connected or not self.imap_client:
                logger.error("Gmail client not connected")
                return {
                    "status": "error",
                    "error": "Not connected to Gmail",
                    "otp": None
                }
            
            otp = self.imap_client.extract_otp(sender_filter, timeout_seconds)
            
            if otp:
                logger.info(f"🔑 OTP extracted: {otp}")
                return {
                    "status": "success",
                    "otp": otp
                }
            else:
                logger.warning(f"OTP not found within {timeout_seconds}s")
                return {
                    "status": "timeout",
                    "error": f"OTP not found within {timeout_seconds}s",
                    "otp": None
                }
                
        except Exception as e:
            logger.error(f"Failed to extract OTP: {e}")
            return {
                "status": "error",
                "error": str(e),
                "otp": None
            }

    async def mark_email_as_read(self, msg_id: str, mailbox: str = "INBOX") -> Dict[str, Any]:
        """
        Mark an email as read.
        
        Args:
            msg_id: Message ID to mark as read
            mailbox: Mailbox name (default: INBOX)
            
        Returns:
            Dictionary with operation status
        """
        try:
            if not self.is_connected or not self.imap_client:
                logger.error("Gmail client not connected")
                return {
                    "status": "error",
                    "error": "Not connected to Gmail"
                }
            
            success = self.imap_client.mark_as_read(msg_id, mailbox)
            
            if success:
                logger.debug(f"✅ Email {msg_id} marked as read")
                return {
                    "status": "success",
                    "msg_id": msg_id,
                    "marked_as_read": True
                }
            else:
                return {
                    "status": "failed",
                    "msg_id": msg_id,
                    "error": "Failed to mark email as read"
                }
                
        except Exception as e:
            logger.error(f"Exception marking email as read: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def disconnect(self) -> None:
        """Disconnect from Gmail servers."""
        try:
            if self.imap_client:
                self.imap_client.close()
                logger.info("Gmail IMAP connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error disconnecting from Gmail: {e}")
