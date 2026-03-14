"""Tool for extracting OTP codes from Gmail."""

from typing import Optional, Dict
from loguru import logger
from dotenv import load_dotenv
load_dotenv()


async def extract_otp(
    imap_client,
    sender_filter: Optional[str] = None,
    timeout_seconds: int = 120,
) -> Dict:
    """
    Extract OTP from recent emails.

    Args:
        imap_client: GmailIMAPClient instance
        sender_filter: Optional sender email filter
        timeout_seconds: Timeout for OTP extraction (default: 120)

    Returns:
        Dictionary with OTP or error
    """
    try:
        otp = imap_client.extract_otp(sender_filter, timeout_seconds)

        if otp:
            logger.info(f"OTP extracted successfully")
            return {
                "status": "success",
                "otp": otp,
            }
        else:
            return {
                "status": "timeout",
                "otp": None,
                "timeout_seconds": timeout_seconds,
            }
    except Exception as e:
        logger.error(f"Failed to extract OTP: {e}")
        return {
            "status": "error",
            "error": str(e),
            "otp": None,
        }
