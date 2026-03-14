"""Tool for extracting recruiter contact information from LinkedIn."""

from typing import Dict, Optional
from loguru import logger
import re


async def extract_recruiter_email(
    browser,
    profile_url: str,
) -> Dict:
    """
    Extract recruiter email from LinkedIn profile.

    Args:
        browser: StealthBrowser instance
        profile_url: LinkedIn profile URL

    Returns:
        Dictionary with contact information
    """
    try:
        await browser.goto_with_delay(profile_url)

        # Wait for profile to load
        if not await browser.wait_for_selector("[data-profile-id]"):
            logger.warning("Profile not found")
            return {
                "status": "not_found",
                "email": None,
                "phone": None,
            }

        # Try to find contact information section
        content = await browser.get_content()

        if not content:
            return {
                "status": "error",
                "email": None,
                "phone": None,
            }

        # Extract email using regex
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        email_match = re.search(email_pattern, content)
        email = email_match.group(0) if email_match else None

        logger.info(f"Extracted recruiter info from {profile_url}")
        return {
            "status": "success",
            "email": email,
            "profile_url": profile_url,
        }

    except Exception as e:
        logger.error(f"Failed to extract recruiter email: {e}")
        return {
            "status": "error",
            "error": str(e),
            "email": None,
            "profile_url": profile_url,
        }
