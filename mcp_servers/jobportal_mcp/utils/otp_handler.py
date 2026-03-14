"""OTP handling for job portal account creation."""

from typing import Optional
from loguru import logger
import asyncio


class OTPHandler:
    """Handle OTP extraction from Gmail for account verification."""

    def __init__(self, gmail_tool_client):
        """
        Initialize OTP handler.

        Args:
            gmail_tool_client: Function to call Gmail MCP tool
        """
        self.gmail_client = gmail_tool_client

    async def get_otp(
        self,
        timeout_seconds: int = 120,
        sender_filter: Optional[str] = None,
    ) -> Optional[str]:
        """
        Extract OTP from Gmail.

        Args:
            timeout_seconds: Timeout for OTP extraction
            sender_filter: Optional sender email filter

        Returns:
            OTP code or None if not found
        """
        try:
            logger.info(f"Waiting for OTP (timeout: {timeout_seconds}s)...")

            # Call Gmail MCP tool to extract OTP
            result = await self.gmail_client.get_otp_code(
                sender_filter=sender_filter,
                timeout_seconds=timeout_seconds,
            )

            if result.get("status") == "success":
                otp = result.get("otp")
                logger.info(f"OTP extracted: {otp}")
                return otp
            else:
                logger.warning(f"OTP extraction failed: {result.get('status')}")
                return None

        except Exception as e:
            logger.error(f"Error getting OTP: {e}")
            return None

    async def wait_and_extract_otp(
        self,
        max_attempts: int = 3,
        timeout_per_attempt: int = 120,
    ) -> Optional[str]:
        """
        Try to extract OTP with retry logic.

        Args:
            max_attempts: Maximum retry attempts
            timeout_per_attempt: Timeout for each attempt

        Returns:
            OTP code or None if all attempts failed
        """
        for attempt in range(max_attempts):
            logger.info(f"OTP extraction attempt {attempt + 1}/{max_attempts}")

            otp = await self.get_otp(timeout_seconds=timeout_per_attempt)
            if otp:
                return otp

            if attempt < max_attempts - 1:
                # Wait before retry
                await asyncio.sleep(10)

        logger.error("OTP extraction failed after all attempts")
        return None
